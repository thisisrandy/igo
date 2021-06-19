"""
Temporary file to hold rewrite of game_manager. Once fleshed out, overwrite
game_manager and remove this file
"""

from constants import COLOR, KEY, KOMI, SIZE
import logging
from chat import ChatThread
from dataclasses import dataclass
from game import Color, Game
from typing import Callable, Coroutine, Dict, Optional
from tornado.websocket import WebSocketHandler
from messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessageType,
    send_outgoing_message,
)
import asyncinit
from db_manager import DbManager, JoinResult
from containers import (
    JoinGameResponseContainer,
    NewGameResponseContainer,
    OpponentConnectedContainer,
)


@dataclass
class ClientData:
    """
    ClientData is a container for all of the various data that a single client
    is concerned with.

    Attributes:

        key: str - the client's player key

        game: Optional[Game] = None - the current game

        chat_thread: Optional[ChatThread] = None - the chat thread associated
        with the current game

        opponent_connected: Optional[bool] = None - whether or not the client's
        opponent in the current game is connected to a game server
    """

    key: str
    game: Optional[Game] = None
    # TODO: add write/load timestamp for keeping track of time played. this
    # might be a bit complicated as we are no longer the sole game manager.
    # possibly this goes in the db, but will need to think it through
    chat_thread: Optional[ChatThread] = None
    opponent_connected: Optional[bool] = None


@asyncinit
class GameStore:
    """
    GameStore is the guts of the in-memory storage and management of games. It
    maps connected clients, identified by their web socket handler, one-to-one
    to all of the data they are concerned with, routes messages, and issues
    responses on the client socket. Although it is possible and indeed likely
    that two clients playing the same game will be connected to the same game
    server, no attempt is made to share data between them above the database
    level.
    """

    async def __init__(self, store_dsn: str) -> None:
        self._clients: Dict[WebSocketHandler, ClientData] = {}
        self._keys: Dict[str, WebSocketHandler] = {}
        self._db_manager: DbManager = await DbManager(
            self._get_game_updater,
            self._get_chat_updater,
            self._get_opponent_connected_updater,
            store_dsn,
        )

    async def new_game(self, msg: IncomingMessage) -> None:
        """
        Create and write out a new game and then respond appropriately
        """

        if msg.websocket_handler in self._clients:
            old_key = self._clients[msg.websocket_handler].key
            logging.info(f"Client requesting new game already subscribed to {old_key}")
            await self.unsubscribe(msg.websocket_handler)

        game = Game(msg.data[SIZE], msg.data[KOMI])
        chat_thread = ChatThread()
        opponent_connected = False
        requested_color = Color[msg.data[COLOR]]
        keys: Dict[Color, str] = await self._db_manager.write_new_game(
            game, requested_color
        )
        client_key = keys[requested_color]
        client = msg.websocket_handler
        self._clients[client] = ClientData(
            client_key, game, chat_thread, opponent_connected
        )
        self._keys[client_key] = client

        # TODO: If msg.data[VS] is "computer", set up computer as second player

        await send_outgoing_message(
            OutgoingMessageType.new_game_response,
            NewGameResponseContainer(
                True,
                (
                    f"Successfully created new game. Make sure to give the"
                    f" {requested_color.inverse().name} player key"
                    f" ({keys[requested_color.inverse()]}) to your opponent so that"
                    f" they can join the game. Your key is {keys[requested_color]}."
                    f" Make sure to write it down in case you want to pause the game"
                    f" and resume it later, or if you want to view it once complete"
                ),
                keys,
                requested_color,
            ),
            client,
        )
        await send_outgoing_message(OutgoingMessageType.game_status, game, client)
        # NOTE: while it might seem like sending an empty chat thread and
        # obviously false connectedness for the client's component could be
        # avoided with defaults on the client side, this is only the case if the
        # client hadn't previously been playing another game. the frontend
        # design strategy is for it to know as little as possible about what's
        # going on, instead just receiving state updates and adjusting its
        # display accordingly. without sending these updates, we require the
        # client to understand that a new game has started and set its own state
        # independently, which breaks the design strategy
        await send_outgoing_message(OutgoingMessageType.chat, chat_thread, client)
        await send_outgoing_message(
            OutgoingMessageType.opponent_connected,
            OpponentConnectedContainer(opponent_connected),
            client,
        )

    def _get_game_updater(self) -> Callable[[str, Game], Coroutine]:
        """
        Return a function which takes a player key string and a Game object,
        updates the in-memory store, and alerts the client of the change. May be
        readily used to generate a subscription callback
        """

        async def callback(player_key: str, game: Game) -> None:
            client = self._updater_callback_preamble(player_key)
            if client:
                self._clients[client].game = game
                logging.info(f"Successfully updated game for player key {player_key}")

                await send_outgoing_message(
                    OutgoingMessageType.game_status, game, client
                )

        return callback

    def _get_chat_updater(self) -> Callable[[str, ChatThread], Coroutine]:
        """
        Return a function which takes a player key string and a ChatThread
        object, updates the in-memory store, and alerts the client of the
        change. Maybe be readily used to generate a subscription callback
        """

        async def callback(player_key: str, thread: ChatThread) -> None:
            client = self._updater_callback_preamble(player_key)
            if client:
                self._clients[client].chat_thread.extend(thread)
                logging.info(
                    f"Successfully updated chat thread for player key {player_key}"
                )

                await send_outgoing_message(OutgoingMessageType.chat, thread, client)

        return callback

    def _get_opponent_connected_updater(self) -> Callable[[str, bool], Coroutine]:
        """
        Return a function which takes a player key string and a bool, updates
        the in-memory store, and alerts the client of the change. Maybe be
        readily used to generate a subscription callback
        """

        async def callback(player_key: str, opponent_connected: bool) -> None:
            client = self._updater_callback_preamble(player_key)
            if client:
                self._clients[client].opponent_connected = opponent_connected
                logging.info(
                    "Successfully updated opponent connected status to"
                    f" {opponent_connected} for player key {player_key}"
                )

                await send_outgoing_message(
                    OutgoingMessageType.opponent_connected,
                    OpponentConnectedContainer(opponent_connected),
                    client,
                )

        return callback

    def _updater_callback_preamble(self, player_key: str) -> Optional[WebSocketHandler]:
        """
        All updater callbacks begin by doing the same couple things. Rather than
        copy-pasting, call this preamble instead
        """

        if player_key not in self._keys:
            logging.warn(f"Player key {player_key} is not being managed by this store")
            return None

        return self._keys[player_key]

    async def join_game(self, msg: IncomingMessage) -> None:
        key: str = msg.data[KEY]
        client: WebSocketHandler = msg.websocket_handler
        if client in self._clients and self._clients[client].key == key:
            await send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    False,
                    f"You are already playing using that key ({key})",
                ),
                client,
            )
        else:
            res: JoinResult
            keys: Optional[Dict[Color, str]]
            res, keys = await self._db_manager.join_game(key)
            if res is JoinResult.dne:
                await send_outgoing_message(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        False,
                        (
                            f"A game corresponding to key {key} was not found. Please"
                            " double-check and try again"
                        ),
                    ),
                    client,
                )
            elif res is JoinResult.in_use:
                await send_outgoing_message(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        False,
                        f"Someone else is already playing using that key ({key})",
                    ),
                    client,
                )
            elif res is JoinResult.success:
                if client in self._clients:
                    old_key = self._clients[client].key
                    logging.info(
                        f"Client requesting join game already subscribed to {old_key}"
                    )
                    await self.unsubscribe(client)

                self._clients[client] = ClientData(key)
                self._keys[key] = client
                color = Color.white if keys[Color.white] == key else Color.black

                await send_outgoing_message(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        True,
                        f"Successfully (re)joined the game as {color.name}",
                        keys,
                        color,
                    ),
                    client,
                )

                await self._db_manager.trigger_update_all(key)
            else:
                raise TypeError(f"Unknown JoinResult {res} encountered")

    async def route_message(self, msg: IncomingMessage) -> None:
        pass

    async def unsubscribe(self, socket: WebSocketHandler) -> None:
        if socket in self._clients:
            key = self._clients[socket].key
            del self._clients[socket]
            del self._keys[key]
            await self._db_manager.unsubscribe(key)
            logging.info(f"Unsubscribed client from key {key}")
        else:
            logging.info("Client with no active subscriptions dropped")


class GameManager:
    """
    GameManager is the simplified Game API to the connection_manager module.
    Its only responsibilites are routing messages to the underlying store

    Attributes:

        store: GameStore - the game store
    """

    async def __init__(self, store_dsn: str) -> None:
        """
        Arguments:

            store_dsn: str - the data source name url of the store database
        """

        self.store: GameStore = await GameStore(store_dsn)

    async def unsubscribe(self, socket: WebSocketHandler) -> None:
        """Unsubscribe the socket from its key if it is subscribed, otherwise
        do nothing"""

        await self.store.unsubscribe(socket)

    async def route_message(self, msg: IncomingMessage) -> None:
        """Route the message to the correct method on the underlying store"""

        if msg.message_type is IncomingMessageType.new_game:
            await self.store.new_game(msg)
        elif msg.message_type is IncomingMessageType.join_game:
            await self.store.join_game(msg)
        elif msg.message_type in (
            IncomingMessageType.game_action,
            IncomingMessageType.chat_message,
        ):
            await self.store.route_message(msg)
        else:
            raise TypeError(
                f"Unknown incoming message type {msg.message_type} encountered"
            )

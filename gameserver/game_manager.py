from .constants import ACTION_TYPE, COLOR, COORDS, KEY, KOMI, MESSAGE, SIZE
import logging
from .chat import ChatMessage, ChatThread
from dataclassy import dataclass
from .game import Action, ActionType, Color, Game
from typing import Callable, Coroutine, Dict, Optional, Tuple
from tornado.websocket import WebSocketHandler
from .messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessage,
    OutgoingMessageType,
)
from asyncinit import asyncinit
from .db_manager import DbManager, JoinResult
from .containers import (
    ActionResponseContainer,
    GameStatusContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
    OpponentConnectedContainer,
)


@dataclass(slots=True)
class ClientData:
    """
    ClientData is a container for all of the various data that a single client
    is concerned with.

    Attributes:

        key: str - the client's player key

        color: Color - the client's color

        game: Optional[Game] = None - the current game

        time_played: Optional[float] = None - the time in seconds that the game
        has been actively played thus far

        chat_thread: Optional[ChatThread] = None - the chat thread associated
        with the current game

        opponent_connected: Optional[bool] = None - whether or not the client's
        opponent in the current game is connected to a game server
    """

    key: str
    color: Color
    game: Optional[Game] = None
    time_played: Optional[float] = None
    chat_thread: Optional[ChatThread] = None
    opponent_connected: Optional[bool] = None

    def __post_init__(self) -> None:
        self.chat_thread = ChatThread(is_complete=True)


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

    __slots__ = ("_clients", "_keys", "_db_manager")

    async def __init__(
        self, store_dsn: str, run_db_setup_scripts: bool = False
    ) -> None:
        self._clients: Dict[WebSocketHandler, ClientData] = {}
        self._keys: Dict[str, WebSocketHandler] = {}
        self._db_manager: DbManager = await DbManager(
            self._get_game_updater(),
            self._get_chat_updater(),
            self._get_opponent_connected_updater(),
            store_dsn,
            run_db_setup_scripts,
        )

    async def new_game(self, msg: IncomingMessage) -> None:
        """
        Create and write out a new game and then respond appropriately
        """

        client = msg.websocket_handler
        old_key = self._clients[client].key if client in self._clients else None

        game = Game(msg.data[SIZE], msg.data[KOMI])
        time_played = 0.0
        chat_thread = ChatThread(is_complete=True)
        opponent_connected = False
        requested_color = Color[msg.data[COLOR]]

        keys: Dict[Color, str] = await self._db_manager.write_new_game(
            game, requested_color, old_key
        )
        if old_key:
            logging.info(f"Client requesting new game already subscribed to {old_key}")
            await self.unsubscribe(client, True)

        client_key = keys[requested_color]
        self._clients[client] = ClientData(
            client_key,
            requested_color,
            game,
            time_played,
            chat_thread,
            opponent_connected,
        )
        self._keys[client_key] = client

        # TODO: If msg.data[VS] is "computer", set up computer as second player

        await OutgoingMessage(
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
        ).send()

        await OutgoingMessage(
            OutgoingMessageType.game_status,
            GameStatusContainer(game, time_played),
            client,
        ).send()
        await OutgoingMessage(OutgoingMessageType.chat, chat_thread, client).send()
        await OutgoingMessage(
            OutgoingMessageType.opponent_connected,
            OpponentConnectedContainer(opponent_connected),
            client,
        ).send()

    def _get_game_updater(self) -> Callable[[str, Game, float], Coroutine]:
        """
        Return a function which takes a player key string, a Game object, and
        the time in seconds that the game has been played thus far, updates the
        in-memory store, and alerts the client of the change. May be readily
        used to generate a subscription callback
        """

        async def callback(player_key: str, game: Game, time_played: float) -> None:
            client = self._updater_callback_preamble(player_key)
            self._clients[client].game = game
            self._clients[client].time_played = time_played
            logging.info(f"Successfully updated game for player key {player_key}")

            await OutgoingMessage(
                OutgoingMessageType.game_status,
                GameStatusContainer(game, time_played),
                client,
            ).send()

        return callback

    def _get_chat_updater(self) -> Callable[[str, ChatThread], Coroutine]:
        """
        Return a function which takes a player key string and a ChatThread
        object, updates the in-memory store, and alerts the client of the
        change. Maybe be readily used to generate a subscription callback
        """

        async def callback(player_key: str, thread: ChatThread) -> None:
            client = self._updater_callback_preamble(player_key)
            self._clients[client].chat_thread.extend(thread)
            logging.info(
                f"Successfully updated chat thread for player key {player_key}"
            )

            await OutgoingMessage(OutgoingMessageType.chat, thread, client).send()

        return callback

    def _get_opponent_connected_updater(self) -> Callable[[str, bool], Coroutine]:
        """
        Return a function which takes a player key string and a bool, updates
        the in-memory store, and alerts the client of the change. Maybe be
        readily used to generate a subscription callback
        """

        async def callback(player_key: str, opponent_connected: bool) -> None:
            client = self._updater_callback_preamble(player_key)
            self._clients[client].opponent_connected = opponent_connected
            logging.info(
                "Successfully updated opponent connected status to"
                f" {opponent_connected} for player key {player_key}"
            )

            await OutgoingMessage(
                OutgoingMessageType.opponent_connected,
                OpponentConnectedContainer(opponent_connected),
                client,
            ).send()

        return callback

    def _updater_callback_preamble(self, player_key: str) -> WebSocketHandler:
        """
        All updater callbacks begin by doing the same couple things. Rather than
        copy-pasting, call this preamble instead
        """

        assert (
            player_key in self._keys
        ), f"Player key {player_key} is not being managed by this store"
        return self._keys[player_key]

    async def join_game(self, msg: IncomingMessage) -> None:
        key: str = msg.data[KEY]
        client: WebSocketHandler = msg.websocket_handler
        if client in self._clients and self._clients[client].key == key:
            await OutgoingMessage(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    False,
                    f"You are already playing using that key ({key})",
                ),
                client,
            ).send()
        else:

            old_key = self._clients[client].key if client in self._clients else None
            res: JoinResult
            keys: Optional[Dict[Color, str]]
            res, keys = await self._db_manager.join_game(key, old_key)

            if res is JoinResult.dne:
                await OutgoingMessage(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        False,
                        (
                            f"A game corresponding to key {key} was not found. Please"
                            " double-check and try again"
                        ),
                    ),
                    client,
                ).send()
            elif res is JoinResult.in_use:
                await OutgoingMessage(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        False,
                        f"Someone else is already playing using that key ({key})",
                    ),
                    client,
                ).send()
            elif res is JoinResult.success:
                if old_key:
                    logging.info(
                        f"Client requesting join game already subscribed to {old_key}"
                    )
                    await self.unsubscribe(client, True)

                color = Color.white if keys[Color.white] == key else Color.black
                self._clients[client] = ClientData(key, color)
                self._keys[key] = client

                await OutgoingMessage(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        True,
                        f"Successfully (re)joined the game as {color.name}",
                        keys,
                        color,
                    ),
                    client,
                ).send()

                await self._db_manager.trigger_update_all(key)
            else:
                raise TypeError(f"Unknown JoinResult {res} encountered")

    async def route_message(self, msg: IncomingMessage) -> None:
        key = msg.data[KEY]
        client = msg.websocket_handler

        assert key in self._keys, f"Received message with unknown key {key}"
        assert (
            client in self._clients
        ), f"Received message from a client who isn't subscribed to anything"
        assert self._clients[client].key == key, (
            f"Received message with key {key} from a client who isn't subscribed to"
            " that key"
        )

        client_data = self._clients[client]
        color = client_data.color

        if msg.message_type is IncomingMessageType.game_action:
            success, explanation = client_data.game.take_action(
                Action(
                    ActionType[msg.data[ACTION_TYPE]],
                    color,
                    msg.timestamp,
                    tuple(msg.data[COORDS])
                    if COORDS in msg.data and msg.data[COORDS]
                    else None,
                )
            )
            logging.info(
                f"Took action with result success={success}, explanation={explanation}"
            )

            if success:
                time_played: Optional[float] = await self._db_manager.write_game(
                    client_data.key, client_data.game
                )
                if time_played is None:
                    success = False
                    explanation = "Game action was preempted by other player"
                else:
                    client_data.time_played = time_played

            await OutgoingMessage(
                OutgoingMessageType.game_action_response,
                ActionResponseContainer(success, explanation),
                client,
            ).send()

            if success:
                await OutgoingMessage(
                    OutgoingMessageType.game_status,
                    GameStatusContainer(client_data.game, time_played),
                    client,
                ).send()
        elif msg.message_type is IncomingMessageType.chat_message:
            message_text = msg.data[MESSAGE]
            await self._db_manager.write_chat(
                client_data.key, ChatMessage(msg.timestamp, color, message_text)
            )
        else:
            raise TypeError(f"Cannot handle messages of type {msg.message_type}")

    async def unsubscribe(
        self, socket: WebSocketHandler, listeners_only: bool = False
    ) -> None:
        """
        Unsubscribe the client identified by socket from their key, if any.
        `listeners_only` is passed to `DbManager.unsubscribe`. See its
        documentation for details
        """

        if socket in self._clients:
            key = self._clients[socket].key
            await self._db_manager.unsubscribe(key, listeners_only)
            del self._clients[socket]
            del self._keys[key]
            logging.info(f"Unsubscribed client from key {key}")
        else:
            logging.info("Client with no active subscriptions dropped")


@asyncinit
class GameManager:
    """
    GameManager is the simplified Game API to the connection_manager module.
    Its only responsibilites are routing messages to the underlying store

    Attributes:

        store: GameStore - the game store
    """

    __slots__ = "store"

    async def __init__(
        self, store_dsn: str, run_db_setup_scripts: bool = False
    ) -> None:
        """
        Arguments:

            store_dsn: str - the data source name url of the store database
        """

        self.store: GameStore = await GameStore(store_dsn, run_db_setup_scripts)

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

"""
Temporary file to hold rewrite of game_manager. Once fleshed out, overwrite
game_manager and remove this file
"""

from game_manager import NewGameResponseContainer
from constants import COLOR, KOMI, SIZE
import logging
from chat import ChatThread
from dataclasses import dataclass
from game import Color, Game
from typing import Dict, Optional
from tornado.websocket import WebSocketHandler
from messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessageType,
    send_outgoing_message,
)
import asyncinit
from db_manager import DbManager


@dataclass
class ClientData:
    """
    ClientData is a container for all of the various data that a single client
    is concerned with.

    Attributes:

        key: str - the client's player key

        game: Game - the current game

        chat_thread: ChatThread - the chat thread associated with the current game

        opponent_connected: bool - whether or not the client's opponent in the
        current game is connected to a game server
    """

    key: str
    game: Game
    chat_thread: ChatThread
    opponent_connected: bool


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
        self._db_manager: DbManager = await DbManager(store_dsn)

    async def new_game(self, msg: IncomingMessage) -> None:
        """
        Create and write out a new game and then respond appropriately
        """

        if msg.websocket_handler in self._clients:
            old_key = self._clients[msg.websocket_handler].key
            logging.info(f"Client requesting new game already subscribed to {old_key}")
            await self.unsubscribe(msg.websocket_handler)

        game = Game(msg.data[SIZE], msg.data[KOMI])
        requested_color = Color[msg.data[COLOR]]
        keys: Dict[Color, str] = await self._db_manager.write_new_game(
            game, requested_color
        )
        client_key = keys[requested_color]
        self._clients[msg.websocket_handler] = ClientData(
            client_key, game, ChatThread()
        )
        self._keys[client_key] = msg.websocket_handler

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
            msg.websocket_handler,
        )

    async def join_game(self, msg: IncomingMessage) -> None:
        pass

    async def route_message(self, msg: IncomingMessage) -> None:
        pass

    async def unsubscribe(self, socket: WebSocketHandler) -> None:
        pass


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

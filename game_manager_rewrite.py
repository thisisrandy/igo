"""
Temporary file to hold rewrite of game_manager. Once fleshed out, overwrite
game_manager and remove this file
"""

from tornado.websocket import WebSocketHandler
from messages import IncomingMessage, IncomingMessageType
import asyncinit


@asyncinit
class GameStore:
    """
    GameStore is the guts of the in-memory storage and management of games. It
    maps connected clients, identified by their web socket handler, one-to-one
    to all of the data they are concerned with, noting that a client who has not
    yet created or joined a game will be mapped to a unique empty data set.
    Although it is possible and indeed likely that two clients playing the same
    game will be connected to the same game server, no attempt is made to share
    data between them above the database level.
    """

    async def __init__(self, store_dsn: str) -> None:
        pass

    async def new_game(self, msg: IncomingMessage) -> None:
        pass

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

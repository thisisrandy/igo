from constants import ACTION_TYPE, COLOR, COORDS, KEY, KEY_LEN, KOMI, SIZE
from messages import (
    IncomingMessage,
    IncomingMessageType,
    JsonifyableBase,
    OutgoingMessageType,
    send_outgoing_message,
)
from uuid import uuid4
from typing import Any, Dict, Optional, Tuple
from game import Action, ActionType, Color, Game
import os
import logging
from dataclasses import dataclass
import pickle
from tornado.websocket import WebSocketHandler
from datetime import datetime
import asyncio
import aiofiles
from asyncinit import asyncinit
from contextlib import AsyncExitStack


@dataclass
class ResponseContainer(JsonifyableBase):
    """
    A base container for responses which implements jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success
    """

    success: bool
    explanation: str

    def jsonifyable(self):
        return {"success": self.success, "explanation": self.explanation}


@dataclass
class GameResponseContainer(ResponseContainer):
    """
    A base container for the response to a game request which implements
    jsonifyable

    Attributes:

        success: bool - whether or not the request succeeded

        explanation: str - an explanatory string

        keys: Optional[Dict[Color, str]] = None - if success, a color to key
        mapping, and None otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    keys: Optional[Dict[Color, str]] = None
    your_color: Optional[Color] = None

    def jsonifyable(self):
        return {
            **{
                "keys": {k.name: v for k, v in self.keys.items()}
                if self.keys
                else None,
                "your_color": self.your_color.name if self.your_color else None,
            },
            **super().jsonifyable(),
        }


@dataclass
class NewGameResponseContainer(GameResponseContainer):
    """
    A container for the response to a new game request which implements
    jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success

        keys: Optional[Dict[Color, str]] = None - if success, a color to key
        mapping, and None otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    pass


@dataclass
class JoinGameResponseContainer(GameResponseContainer):
    """
    A container for the response to a join game request which implements
    jsonifyable

    Attributes:

        success: bool - whether or not the join request succeeded

        explanation: str - an explanatory string

        keys: Optional[Dict[Color, str]] = None - if success, a color to key
        mapping, and None otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    pass


@dataclass
class ActionResponseContainer(ResponseContainer):
    """
    A container for the response from Game.take_action which implements
    jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success
    """

    pass


class GameStatusContainer(JsonifyableBase):
    """
    A container for game status updates. Augments Game with opponentConnected,
    an indicator of whether or not the player's opponent is currently connected
    to the game
    """

    def __init__(self, game: Game, num_subscribers: int) -> None:
        self._game = game
        self._opponent_connected = num_subscribers == 2

    def jsonifyable(self) -> Any:
        return {
            **self._game.jsonifyable(),
            **{"opponentConnected": self._opponent_connected},
        }

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False
        return (
            self._game == o._game and self._opponent_connected == o._opponent_connected
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"game={self._game}"
            f", opponent_connected={self._opponent_connected})"
        )


@asyncinit
class GameContainer:
    """
    A container for Games. Responsible for loading from disk and unloading on
    demand (externally controlled), writing to disk as needed, and passing
    messages between the requesting client and the contained game

    Attributes:

        game: Game - the contained Game object

        keys: Dict[Color, str] - a maping from colors to keys

        colors: Dict[str, Color] - a mapping from keys to colors (inverse of keys)
    """

    async def __init__(
        self, filepath: str, keys: Dict[Color, str], game: Optional[Game] = None
    ) -> None:
        """
        Arguments:

            filepath: str - the path to read from and write to

            keys: Dict[Color, str] - a mapping from colors to keys

            game: Optional[Game] - if provided, game is treated as a new game
            and immediately written to disk
        """

        self._filepath: str = filepath
        self.keys = keys
        self.colors: Dict[str, Color] = {
            keys[Color.white]: Color.white,
            keys[Color.black]: Color.black,
        }
        self.game: Optional[Game] = game
        self._filename = os.path.basename(self._filepath)
        # we set this whenever we write or load and unset on unload. if there
        # was a previously set timestamp when we go to write, add the difference
        # to the game's time_played
        self._write_load_timestamp = None
        self._lock = asyncio.Lock()

        if self.game:
            logging.info(f"Created new game {self._filename}")
            await self._write()

    def __hash__(self) -> int:
        return hash(self._filename)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False
        return o._filepath == self._filepath

    def __repr__(self) -> str:
        return (
            f"GameContainer(filepath={self._filepath}"
            f", colors={self.colors}"
            f", game={self.game})"
        )

    async def load(self) -> None:
        async with self._lock:
            if self._is_loaded():
                logging.warning(f"Tried to load already loaded game {self._filename}")
                return

            async with aiofiles.open(self._filepath, "rb") as reader:
                pickled_game = await reader.read()
            self.game = pickle.loads(pickled_game)

            self._write_load_timestamp = datetime.now().timestamp()

        logging.info(f"Loaded game {self._filename}")

    async def unload(self) -> None:
        async with self._lock:
            if not self._is_loaded():
                logging.warning(f"Tried to unload already unload game {self._filename}")
                return

            self.game = None
            self._write_load_timestamp = None

        logging.info(f"Unloaded game {self._filename}")

    async def _write(self, use_lock=True) -> None:
        """Set use_lock to False if already holding self._lock"""

        async with AsyncExitStack() as stack:
            if use_lock:
                await stack.enter_async_context(self._lock)

            self._assert_loaded("write")

            ts = datetime.now().timestamp()
            if self._write_load_timestamp:
                self.game.add_time_played(ts - self._write_load_timestamp)

            async with aiofiles.open(self._filepath, "wb") as writer:
                pickled_game = pickle.dumps(self.game)
                await writer.write(pickled_game)

            self._write_load_timestamp = ts

        logging.info(f"Wrote game {self._filename} to disk")

    def _is_loaded(self) -> bool:
        return self.game is not None

    def _assert_loaded(self, action: str) -> None:
        assert (
            self._is_loaded()
        ), f"Attempted to {action} unloaded game {self._filename}"

    async def pass_message(self, msg: IncomingMessage) -> bool:
        """Translate msg into a game action, attempt to take that action, and
        reply with the game's response. Return True if the action was
        successful and False otherwise"""

        async with self._lock:
            self._assert_loaded("pass message to")
            assert (
                msg.message_type is IncomingMessageType.game_action
            ), f"{self.__class__.__name__} can only process game actions"

            success, explanation = self.game.take_action(
                Action(
                    ActionType[msg.data[ACTION_TYPE]],
                    self.colors[msg.data[KEY]],
                    msg.timestamp,
                    tuple(msg.data[COORDS]) if COORDS in msg.data else None,
                )
            )

            logging.info(
                f"Took action with result success={success}, explanation={explanation}"
            )
            logging.debug(f"Game state is now {self.game}")

            # note that we want to write even after unsuccessful actions in order to
            # update time played
            await self._write(use_lock=False)

        await send_outgoing_message(
            OutgoingMessageType.game_action_response,
            ActionResponseContainer(success, explanation),
            msg.websocket_handler,
        )

        return success


@asyncinit
class GameStore:
    """
    The interface storing and routing messages to GameContainer objects.
    Responsible for populating the games list from disk and managing
    subscriptions to game keys

    Attributes:

        dir: str - the store directory. a Game g is stored in pickled form at
        store_dir/{g.keys[Color.white]}{g.keys[Color.black]} and is read and
        written as needed

        keys: Dict[str, GameContainer] - the in-memory store mapping keys to
        their respective Games

        containers: Dict[GameContainer, Tuple[str, str]] - reverse of keys,
        useful for routing status updates

        subscriptions: Dict[str, WebSocketHandler] - key to client mapping

        clients: Dict[WebSocketHandler, str] - reverse of subscriptions,
        useful for unsubscribing when a connection is closed
    """

    async def __init__(self, dir: str) -> None:
        self.dir: str = dir
        self.keys: Dict[str, GameContainer] = {}
        self.containers: Dict[GameContainer, Tuple[str, str]] = {}
        self.subscriptions: Dict[str, WebSocketHandler] = {}
        self.clients: Dict[WebSocketHandler, str] = {}
        await self._hydrate_games()

    async def _hydrate_games(self) -> None:
        """List the contents of self.store_dir and enumerate the available
        games. Should only be called once by __init__"""

        for f in os.listdir(self.dir):
            path = os.path.join(self.dir, f)
            if not os.path.isfile(path):
                logging.warning(
                    f"The store directory ({self.dir}) should only contain files, but a"
                    " directory ({f}) was found. Ignoring"
                )
                continue
            if len(f) != KEY_LEN * 2:
                logging.warning(
                    f"Found a file with a name of the wrong length ({f}, expected"
                    " length {KEY_LEN*2}). Ignoring"
                )

            key_w, key_b = f[:KEY_LEN], f[KEY_LEN:]
            assert (
                key_w not in self.keys and key_b not in self.keys
            ), "Duplicate key, blowing up"

            gc = await GameContainer(path, {Color.white: key_w, Color.black: key_b})
            self.keys[key_w] = self.keys[key_b] = gc
            self.containers[gc] = (key_w, key_b)

            logging.info(f"Discovered game {f} in store {self.dir}")

    async def route_message(self, msg: IncomingMessage) -> None:
        key = msg.data[KEY]

        assert key in self.keys, f"Received message with unknown key {key}"
        assert key in self.subscriptions, f"No one is subscribed to {key}"
        assert self.subscriptions[key] == msg.websocket_handler, (
            f"Received message with key {key} from a client who isn't subscribed to"
            " that key"
        )

        if await self.keys[key].pass_message(msg):
            await self._send_game_status(self.keys[key])

    async def _send_game_status(self, gc: GameContainer) -> None:
        """Send a game status message to any subscribers to gc"""

        for key in self.containers[gc]:
            if key in self.subscriptions:
                await send_outgoing_message(
                    OutgoingMessageType.game_status,
                    GameStatusContainer(gc.game, self._num_subscribers(gc)),
                    self.subscriptions[key],
                )

    async def new_game(
        self, msg: IncomingMessage, _keys: Dict[Color, str] = None
    ) -> None:
        """
        Create a new GameContainer according to the specification in msg,
        store it in our routing tables, and respond appropriately.

        NB: _keys is for testing purposes only. in production, randomly
        generated keys should always be used
        """

        if _keys:
            key_w, key_b = _keys[Color.white], _keys[Color.black]
            keys = _keys
        else:
            key_w, key_b = [uuid4().hex[-KEY_LEN:] for _ in range(2)]
            keys = {Color.white: key_w, Color.black: key_b}

        assert (
            key_w not in self.keys and key_b not in self.keys
        ), "Duplicate key, blowing up"

        if msg.websocket_handler in self.clients:
            old_key = self.clients[msg.websocket_handler]
            logging.info(f"Client requesting new game already subscribed to {old_key}")
            await self.unsubscribe(msg.websocket_handler)

        path = os.path.join(self.dir, f"{key_w}{key_b}")
        gc = await GameContainer(path, keys, Game(msg.data[SIZE], msg.data[KOMI]))
        requested_color = Color[msg.data[COLOR]]

        self.keys[key_w] = self.keys[key_b] = gc
        self.containers[gc] = (key_w, key_b)
        self.subscriptions[keys[requested_color]] = msg.websocket_handler
        self.clients[msg.websocket_handler] = keys[requested_color]

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

        await self._send_game_status(gc)

    async def join_game(self, msg: IncomingMessage) -> None:
        """Attempt to subscribe to the key specified in msg and respond
        appropriately"""

        key = msg.data[KEY]
        if key not in self.keys:
            await send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    False,
                    (
                        f"A game corresponding to key {key} was not found. Please"
                        " double-check and try again"
                    ),
                ),
                msg.websocket_handler,
            )
        elif key in self.subscriptions:
            await send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    False,
                    (
                        (
                            "You are"
                            if self.subscriptions[key] is msg.websocket_handler
                            else "Someone else is"
                        )
                        + " already playing that game and color"
                    ),
                ),
                msg.websocket_handler,
            )
        else:
            if msg.websocket_handler in self.clients:
                old_key = self.clients[msg.websocket_handler]
                logging.info(
                    f"Client requesting join game already subscribed to {old_key}"
                )
                await self.unsubscribe(msg.websocket_handler)

            self.subscriptions[key] = msg.websocket_handler
            self.clients[msg.websocket_handler] = key
            gc = self.keys[key]
            color = gc.colors[key]

            await send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    True,
                    f"Successfully (re)joined the game as {color.name}",
                    gc.keys,
                    color,
                ),
                msg.websocket_handler,
            )

            # if we are the first to join this game, e.g. because we are
            # resuming an old game, load it up from disk
            if self._num_subscribers(gc) == 1:
                await gc.load()

            await self._send_game_status(self.keys[key])

    def _num_subscribers(self, gc: GameContainer) -> int:
        """Determine the number of clients actively subscribed to gc"""

        k1, k2 = self.containers[gc]
        return (k1 in self.subscriptions) + (k2 in self.subscriptions)

    async def unsubscribe(self, socket: WebSocketHandler) -> None:
        """If socket is subscribed to a key, unsubscribe it"""

        if socket in self.clients:
            key = self.clients[socket]
            del self.clients[socket]
            del self.subscriptions[key]
            logging.info(f"Unsubscribed client from key {key}")

            # if subscribers has dropped to 0, unload the game. if not, let the
            # other player know that their opponent has left
            gc = self.keys[key]
            if not self._num_subscribers(gc):
                await gc.unload()
            else:
                await self._send_game_status(gc)
        else:
            logging.info("Client with no active subscription dropped")


@asyncinit
class GameManager:
    """
    GameManager is the simplified Game API to the connection_manager module.
    Its only responsibilites are routing messages to the underlying store

    Attributes:

        store: GameStore - the game store
    """

    async def __init__(
        self,
        store_dir: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "store"
        ),
    ) -> None:
        """
        Arguments:

            store: str = (script dir)/store
        """
        if not os.path.exists(store_dir):
            logging.info(f"{store_dir} does not exist. Attempting to create...")
            os.mkdir(store_dir)
        elif not os.path.isdir(store_dir):
            raise NotADirectoryError(f"{store_dir} is not a directory")

        self.store: GameStore = await GameStore(store_dir)

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
        elif msg.message_type is IncomingMessageType.game_action:
            await self.store.route_message(msg)
        else:
            raise TypeError(
                f"Unknown incoming message type {msg.message_type} encountered"
            )

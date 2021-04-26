from constants import ACTION_TYPE, COLOR, COORDS, KEY, KEY_LEN, KOMI
from messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessageType,
    send_outgoing_message,
)
from uuid import uuid4
from typing import Dict, Optional, Tuple
from game import Action, ActionType, Color, Game
import os
import logging
from dataclasses import dataclass
import pickle
from tornado.websocket import WebSocketHandler


@dataclass
class NewGameResponseContainer:
    """
    A container for the response to a new game request which implements
    jsonifyable

    Attributes:

        keys: Dict[Color, str] - color to newly created key mapping

        your_color: Color - the color that the user is subscribed to
    """

    keys: Dict[Color, str]
    your_color: Color

    def jsonifyable(self) -> Dict[str, str]:
        return {
            "keys": {k.name: v for k, v in self.keys.items()},
            "your_color": self.your_color.name,
        }


@dataclass
class JoinGameResponseContainer:
    """
    A container for the response to a join game request which implements
    jsonifyable

    Attributes:

        success: bool - whether or not the join request succeeded

        explanation: str - an explanatory string

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    success: bool
    explanation: str
    your_color: Optional[Color] = None

    def jsonifyable(self):
        return {
            "success": self.success,
            "explanation": self.explanation,
            "your_color": self.your_color.name if self.your_color else None,
        }


@dataclass
class ActionResponseContainer:
    """
    A container for the response from Game.take_action which implements
    jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success
    """

    success: bool
    explanation: str

    def jsonifyable(self):
        return {"success": self.success, "explanation": self.explanation}


class GameContainer:
    """
    A container for Games. Responsible for loading from disk and unloading on
    demand (externally controlled), writing to disk as needed, and passing
    messages between the requesting client and the contained game

    Attributes:

        game: Game - the contained Game object

        colors: Dict[str, Color] - a mapping from keys to colors
    """

    def __init__(
        self, filepath: str, keys: Dict[Color, str], game: Optional[Game] = None
    ) -> None:
        """
        Arguments:

            filepath: str - the path to read from and write to

            keys: Dict[Color, str] - a mapping from colors to keys

            game: Optional[Game] - if provided, game is treated as a new game
            and immediately written to disk
        """

        # TODO: each game needs a write lock. I think... invesigate tornado in
        # order guarantees and reason a bit about how I'm handling messages

        self._filepath: str = filepath
        self.colors: Dict[str, Color] = {
            keys[Color.white]: Color.white,
            keys[Color.black]: Color.black,
        }
        self.game: Optional[Game] = game
        self._filename = os.path.basename(self._filepath)

        if self.game:
            self._write()

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

    def load(self) -> None:
        if self._is_loaded():
            logging.warn(f"Tried to load already loaded game {self._filename}")
            return

        with open(self._filepath, "rb") as reader:
            self.game = pickle.load(reader)

        logging.info(f"Loaded game {self._filename}")

    def unload(self) -> None:
        if not self._is_loaded():
            logging.warn(f"Tried to unload already unload game {self._filename}")
            return

        self.game = None

        logging.info(f"Unloaded game {self._filename}")

    def _write(self) -> None:
        self._assert_loaded("write")

        with open(self._filepath, "wb") as writer:
            pickle.dump(self.game, writer)

        logging.info(f"Wrote game {self._filename} to disk")

    def _is_loaded(self) -> bool:
        return self.game is not None

    def _assert_loaded(self, action: str) -> None:
        assert (
            self._is_loaded()
        ), f"Attempted to {action} unloaded game {self._filename}"

    def pass_message(self, msg: IncomingMessage) -> bool:
        """Translate msg into a game action, attempt to take that action, and
        reply with the game's response. Return True if the action was
        successful and False otherwise"""

        self._assert_loaded("pass message to")
        assert (
            msg.message_type is IncomingMessageType.game_action
        ), f"{self.__class__.__name__} can only process game actions"

        success, explanation = self.game.take_action(
            Action(
                ActionType[msg.data[ACTION_TYPE]],
                Color[msg.data[COLOR]],
                msg.timestamp,
                tuple(msg.data[COORDS]) if COORDS in msg.data else None,
            )
        )

        logging.info(
            f"Took action with result success={success}, explanation={explanation}"
        )
        logging.debug(f"Game state is now {self.game}")

        if success:
            self._write()

        send_outgoing_message(
            OutgoingMessageType.game_action_response,
            ActionResponseContainer(success, explanation),
            msg.websocket_handler,
        )

        return success


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

    def __init__(self, dir: str) -> None:
        self.dir: str = dir
        self.keys: Dict[str, GameContainer] = {}
        self.containers: Dict[GameContainer, Tuple[str, str]] = {}
        self.subscriptions: Dict[str, WebSocketHandler] = {}
        self.clients: Dict[WebSocketHandler, str] = {}
        self._hydrate_games()

    def _hydrate_games(self) -> None:
        """List the contents of self.store_dir and enumerate the available
        games. Should only be called once by __init__"""

        for f in os.listdir(self.dir):
            path = os.path.join(self.dir, f)
            if not os.path.isfile(path):
                logging.warn(
                    f"The store directory ({self.dir}) should only contain files, but a"
                    " directory ({f}) was found. Ignoring"
                )
                continue
            if len(f) != KEY_LEN * 2:
                logging.warn(
                    f"Found a file with a name of the wrong length ({f}, expected"
                    " length {KEY_LEN*2}). Ignoring"
                )

            key_w, key_b = f[:KEY_LEN], f[KEY_LEN:]
            assert (
                key_w not in self.keys and key_b not in self.keys
            ), "Duplicate key, blowing up"

            gc = GameContainer(path, {Color.white: key_w, Color.black: key_b})
            self.keys[key_w] = self.keys[key_b] = gc
            self.containers[gc] = (key_w, key_b)

    def route_message(self, msg: IncomingMessage) -> None:
        key = msg.data[KEY]

        assert key in self.keys, f"Received message with unknown key {key}"
        assert key in self.subscriptions, f"No one is subscribed to {key}"
        assert self.subscriptions[key] == msg.websocket_handler, (
            f"Received message with key {key} from a client who isn't subscribed to"
            " that key"
        )

        if self.keys[key].pass_message(msg):
            self._send_game_status(self.keys[key])

    def _send_game_status(self, gc: GameContainer) -> None:
        """Send a game status message to any subscribers to gc"""

        for key in self.containers[gc]:
            if key in self.subscriptions:
                send_outgoing_message(
                    OutgoingMessageType.game_status, gc.game, self.subscriptions[key]
                )

    def new_game(self, msg: IncomingMessage, _keys: Dict[Color, str] = None) -> None:
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

        path = os.path.join(self.dir, f"{key_w}{key_b}")
        # TODO: If I decide to support different board sizes, here is the place
        # to plug it in
        gc = GameContainer(path, keys, Game(komi=msg.data[KOMI]))
        requested_color = Color[msg.data[COLOR]]

        self.keys[key_w] = self.keys[key_b] = gc
        self.containers[gc] = (key_w, key_b)
        self.subscriptions[keys[requested_color]] = msg.websocket_handler
        self.clients[msg.websocket_handler] = keys[requested_color]

        # TODO: If msg.data[VS] is "computer", set up computer as second player

        send_outgoing_message(
            OutgoingMessageType.new_game_response,
            NewGameResponseContainer(keys, requested_color),
            msg.websocket_handler,
        )

        self._send_game_status(gc)

    def join_game(self, msg: IncomingMessage) -> None:
        """Attempt to subscribe to the key specified in msg and respond
        appropriately"""

        key = msg.data[KEY]
        if key not in self.keys:
            send_outgoing_message(
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
        elif msg.websocket_handler in self.clients:
            send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    False,
                    (
                        "You are already playing a game using key"
                        f" {self.clients[msg.websocket_handler]}"
                    ),
                ),
                msg.websocket_handler,
            )
        elif key in self.subscriptions:
            send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    False, "Someone else is already playing that game and color"
                ),
                msg.websocket_handler,
            )
        else:
            self.subscriptions[key] = msg.websocket_handler
            self.clients[msg.websocket_handler] = key
            gc = self.keys[key]
            color = gc.colors[key]

            send_outgoing_message(
                OutgoingMessageType.join_game_response,
                JoinGameResponseContainer(
                    True, f"Successfully joined the game as {color.name}", color
                ),
                msg.websocket_handler,
            )

            # if we are the first to join this game, e.g. because we are
            # resuming an old game, load it up from disk
            if self._num_subscribers(gc) == 1:
                gc.load()

            self._send_game_status(self.keys[key])

    def _num_subscribers(self, gc: GameContainer) -> int:
        """Determine the number of clients actively subscribed to gc"""

        k1, k2 = self.containers[gc]
        return (k1 in self.subscriptions) + (k2 in self.subscriptions)

    def unsubscribe(self, socket: WebSocketHandler) -> None:
        """If socket is subscribed to a key, unsubscribe it"""

        if socket in self.clients:
            key = self.clients[socket]
            del self.clients[socket]
            del self.subscriptions[key]

            # if subscribers has dropped to 0, unload the game
            gc = self.keys[key]
            if not self._num_subscribers(gc):
                gc.unload()


class GameManager:
    """
    GameManager is the simplified Game API to the connection_manager module.
    Its only responsibilites are routing messages to the underlying store

    Attributes:

        store: GameStore - the game store
    """

    def __init__(
        self,
        store_dir: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "store"
        ),
    ) -> None:
        """
        Arguments:

            store: str = (script dir)/store
        """

        self.store = GameStore(store_dir)

    def unsubscribe(self, socket: WebSocketHandler) -> None:
        """Unsubscribe the socket from its key if it is subscribed, otherwise
        do nothing"""

        self.store.unsubscribe(socket)

    def route_message(self, msg: IncomingMessage) -> None:
        """Route the message to the correct method on the underlying store"""

        if msg.message_type is IncomingMessageType.new_game:
            self.store.new_game(msg)
        elif msg.message_type is IncomingMessageType.join_game:
            self.store.join_game(msg)
        elif msg.message_type is IncomingMessageType.game_action:
            self.store.route_message(msg)

from constants import ACTION_TYPE, COLOR, COORDS, KEY, KEY_LEN
from messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessage,
    OutgoingMessageType,
)
from uuid import uuid4
from typing import Dict, Optional
from game import Action, ActionType, Color, Game
import os
import logging
from dataclasses import dataclass
import pickle
from tornado.websocket import WebSocketHandler


@dataclass
class ActionResponseContainer:
    """
    A container for the response from Game.take_action which implements jsonifyable

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
    demand (extenally controlled), writing to disk as needed, and passing
    messages between the requesting client and the contained game

    Attributes:

        game: Game - the contained Game object
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
        self._keys: Dict[str, Color] = {
            keys[Color.white]: Color.white,
            keys[Color.black]: Color.black,
        }
        self.game: Optional[Game] = game
        self._filename = os.path.basename(self._filepath)

        if self.game:
            self.write()

    def __hash__(self) -> int:
        return hash(self._filename)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False
        return o._filepath == self._filepath

    def __repr__(self) -> str:
        return (
            f"GameContainer(filepath={self._filepath}"
            f", keys={self._keys}"
            f", game={self.game})"
        )

    def load(self) -> None:
        if self.is_loaded():
            logging.warn(f"Tried to load already loaded game {self._filename}")
            return

        with open(self._filepath, "rb") as reader:
            self.game = pickle.load(reader)

        logging.info(f"Loaded game {self._filename}")

    def unload(self) -> None:
        if not self.is_loaded():
            logging.warn(f"Tried to unload already unload game {self._filename}")
            return

        self.game = None

        logging.info(f"Unloaded game {self._filename}")

    def write(self) -> None:
        self._assert_loaded("write")

        with open(self._filepath, "wb") as writer:
            pickle.dump(self.game, writer)

        logging.info(f"Wrote game {self._filename} to disk")

    def is_loaded(self) -> bool:
        return self.game is not None

    def _assert_loaded(self, action: str) -> None:
        assert self.is_loaded(), f"Attempted to {action} unloaded game {self._filename}"

    def pass_message(self, msg: IncomingMessage) -> bool:
        """Translate msg into a game action, attempt to take that action, and
        reply with the game's response"""

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
            self.write()

        OutgoingMessage(
            OutgoingMessageType.action_response,
            ActionResponseContainer(success, explanation),
            msg.websocket_handler,
        ).send()


class GameStore:
    """
    The interface storing and routing messages to GameContainer objects.
    Responsible for populating the games list from disk and managing
    subscriptions to game keys

    Attributes:

        dir: str - the store directory

        keys: Dict[str, GameContainer] - the in-memory store mapping keys to
        their respective Games

        containers: Dict[GameContainer, str] - reverse of keys, useful for
        managing subscriptions

        subscriptions: Dict[WebSocketHandler, str] -
    """

    def __init__(self, dir: str) -> None:
        self.dir: str = dir
        self.keys: Dict[str, GameContainer] = {}
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

            self.keys[key_w] = self.keys[key_b] = GameContainer(
                path, {Color.white: key_w, Color.black: key_b}
            )

    def route_message(self, msg: IncomingMessage) -> None:
        assert (
            msg.data[KEY] in self.keys
        ), f"Received message with unknown key {msg.data[KEY]}"

        # TODO: check if the caller is subscribed to the key before passing the
        # message

        self.keys[msg.data[KEY]].pass_message(msg)

    def new_game(self, keys: Dict[Color, str]) -> None:
        """Create a new GameContainer and store it in our routing table"""

        # TODO: GameManager doesn't need to know about keys. Move key
        # generation here

        assert (
            keys[Color.white] not in self.keys and keys[Color.black] not in self.keys
        ), "Duplicate key, blowing up"

        path = os.path.join(self.dir, f"{keys[Color.white]}{keys[Color.black]}")
        self.keys[keys[Color.white]] = self.keys[keys[Color.black]] = GameContainer(
            path, keys
        )


class GameManager:
    """
    The GameManager has several responsibilities:

    1. Instantiating new Games
    2. Binding and unbinding Game subscriptions
    3. Handling message routing/translation between ConnectionManager and Game
    4. Pickling and loading Games on modification and on demand, respectively

    Attributes:

        store_dir: str = (script dir)/store - the location of the Game store.
        a Game g is stored in pickled form at
        store_dir/{g.keys[Color.white]}{g.keys[Color.black]} and is read and
        written as needed
    """

    def __init__(
        self,
        store_dir: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "store"
        ),
    ) -> None:
        self.store_dir = store_dir

    def new_game(self, msg: IncomingMessage) -> None:
        """Create a new game and subscribe the caller to the appropriate key"""

        # TODO: I think the correct flow is actually to have one public entry
        # point where we look at the message type and route to the correct
        # private method. Do that instead

        keys: Dict[Color, str] = {
            Color.white: uuid4().hex[-KEY_LEN:],
            Color.black: uuid4().hex[-KEY_LEN:],
        }

    def subscribe(self, msg: IncomingMessage) -> None:
        """Attempt to subscribe the caller to the requested key and reply
        appropriately"""

        pass

    def unsubscribe(self, socket: WebSocketHandler) -> bool:
        """Attempt to unsubscribe the socket from its key. Return True on
        success and False if a subscription is not found"""

        pass

    def pass_message(self, msg: IncomingMessage) -> None:
        """Attempt to route the message and reply appropriately"""

        pass
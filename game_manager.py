from typing import Dict, Optional
from game import Color, Game
import os
import logging
from dataclasses import dataclass
import pickle

KEY_LEN = 10


@dataclass
class GameContainer:
    """
    A container for Games. Responsible for loading and unloading from and
    writing to disk as needed, as well as passing messages

    Attributes:

        filepath: str - the name of the file where the game is stored

        keys: Dict[str, Color] - mapping from key to color

        user_bindings: Optional[Dict[str, Optional[bool]]] - indicator of the
        user id, if any, that each key is bound to. Note: Optional only for
        the sake of using a sentinel as the default to avoid the mutable
        default anti-pattern

        game: Optional[Game] - the Game object, if loaded
    """

    filepath: str
    keys: Dict[Color, str]
    user_bindings: Optional[Dict[str, Optional[str]]] = None
    game: Optional[Game] = None

    def __post_init__(self) -> None:
        self.user_bindings = {key: None for key in self.keys.values()}
        self._filename = os.path.basename(self.filepath)

    def load(self) -> None:
        if self.is_loaded():
            logging.warn(f"Tried to load already loaded game {self._filename}")
            return

        with open(self.filepath, "rb") as reader:
            self.game = pickle.load(reader)

        logging.info(f"Loaded game {self._filename}")

    def unload(self) -> None:
        if not self.is_loaded():
            logging.warn(f"Tried to unload already unload game {self._filename}")
            return

        self.game = None

        logging.info(f"Unloaded game {self._filename}")

    def write(self) -> None:
        if not self.is_loaded():
            raise RuntimeError(f"Attempted to write unloaded game {self._filename}")

        with open(self.filepath, "wb") as writer:
            pickle.dump(self.game, writer)

        logging.info(f"Wrote game {self._filename} to disk")

    def is_loaded(self) -> bool:
        return self.game is not None


class GameStore:
    """
    The interface storing and routing messages to Game objects

    Attributes:

        dir: str - the store directory

        keys: Dict[str, GameContainer] - the in-memory store mapping keys to
        their respective Games
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

    def route_message(key: str, msg: str) -> bool:
        pass


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

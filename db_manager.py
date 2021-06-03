from game import ChatMessage, Color, Game
from typing import Dict, Optional, Tuple
from asyncinit import asyncinit
import asyncpg

# TODO: handle database restarts.
# https://github.com/MagicStack/asyncpg/issues/421 seems to indicate that
# listeners aren't automatically reconnected


@asyncinit
class DbManager:
    async def __init__(self, dsn: str = "postgres://randy@localhost/randy") -> None:
        """
        Interface to the postgres database store. Responsibilities include:

        - On start up:
            * Creating tables and indices if they do not exist
            * Otherwise, cleaning the player key table in case of reboot while
              managing any connections
        - Handling new game creation
        - Handling joining a connected player to an existing game
        - Subscribing to game and chat update channels and registering callbacks for
          each
        - Issuing game updates to the database and reporting success or failure
        - Issuing chat messages to the database
        """

        # TODO: we probably want to use a connection pool instead of a single
        # connection. look into best practices
        self._connection: asyncpg.connection.Connection = await asyncpg.connect(dsn)

    async def create_new_game(self) -> Tuple[bool, Optional[Dict[Color, str]]]:
        """
        Attempt to create a new game. Return a tuple of success or failure
        (on key conflict) and a dictionary of Color: key pairs on success or
        None otherwise
        """

        pass

    async def join_game(self, player_key: str) -> Tuple[bool, str]:
        """
        Attempt to join a game using `player_key`. Return a tuple of success or
        failure and an explanatory message
        """

        pass

    async def _subscribe_to_game_status(self, player_key: str) -> None:
        """
        Subscribe to the game status channel corresponding to `player_key` and
        register a callback to receive game status updates. Should be called
        only after successfully creating or joining a game
        """

        pass

    async def _subcribe_to_chat_feed(self, game_id: int) -> None:
        """
        Subscribe to the chat feed channel corresponding to `game_id` and
        register a callback to receive chat feed updates. Should be called only
        after successfully creating or joining a game
        """

        pass

    async def write_game(self, game: Game) -> bool:
        """
        Attempt to write `game` and increment its version in the database.
        Return True on success and False on failure, i.e. when the write has
        been preempted from another source
        """

        pass

    async def write_chat(self, message: ChatMessage) -> bool:
        """
        Attempt to write `message` to the database. Return True on success and
        False otherwise (unspecified network or database failure)
        """

        pass

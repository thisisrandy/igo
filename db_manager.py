from enum import Enum, auto
from constants import KEY_LEN
from game import ChatMessage, Color, Game
from typing import Any, Callable, Dict, Optional, Tuple
from asyncinit import asyncinit
import asyncpg
from uuid import uuid4
from hashlib import sha256
import asyncio
import pickle
import logging

# TODO: handle database restarts.
# https://github.com/MagicStack/asyncpg/issues/421 seems to indicate that
# listeners aren't automatically reconnected


class JoinResult(Enum):
    """
    dne - the player key requested does not exist
    in_use - someone was already connected to the requested player key
    success - successfully joined using the requested player key
    """

    dne = auto()
    in_use = auto()
    success = auto()


class _UpdateType(Enum):
    game_status = auto()
    chat = auto()


@asyncinit
class DbManager:
    async def __init__(self, dsn: str = "postgres://randy@localhost/randy") -> None:
        """
        Interface to the postgres database store. Responsibilities include:

        - On start up, cleaning the player key table in case of reboot while
          managing any connections
        - Handling new game creation
        - Handling joining a connected player to an existing game
        - Subscribing to game and chat update channels and registering callbacks for
          each
        - Issuing game updates to the database and reporting success or failure
        - Issuing chat messages to the database
        - Unsubscribing from update channels and cleaning up
        """

        # TODO: we probably want to use a connection pool instead of a single
        # connection. look into best practices
        self._connection: asyncpg.connection.Connection = await asyncpg.connect(dsn)

        # machine-id is a reboot persistent unique identifier that should not be
        # shared externally. the following mimics sd_id128_get_machine_app_specific()
        with open("/etc/machine-id", "rb") as r:
            self._machine_id = sha256(r.readline().strip()).hexdigest()

        # if we get restarted while a client is connected to a game, the
        # database will still reflect that we are managing their connection. it
        # is the responsibility of each game server to clean up after itself on
        # restart
        #
        # NOTE: this logic breaks down if a game server never restarts or is
        # replaced by another machine, meaning that a game key can become
        # orphaned without manual intervention. this could be commonplace in
        # certain environments, where some external janitorial watcher would
        # need to be present. for now, we are assuming that the worst that
        # happens to any game server is an unexpected restart
        try:
            await self._connection.execute(
                """
                CALL do_cleanup($1);
                """,
                self._machine_id,
            )

        except Exception as e:
            logging.error(f"Encountered exception during restart cleanup: {e}")

        # set up the notifications queue and consumer
        self._update_queue = asyncio.Queue()
        asyncio.create_task(self._update_consumer())

    async def write_new_game(
        self,
        game: Game,
        player_color: Color = None,
    ) -> Tuple[bool, Optional[Dict[Color, str]]]:
        """
        Attempt to write `game` to the database as a new game. Return a tuple of
        success or failure (on key conflict) and a dictionary of Color: key
        pairs on success or None otherwise. Optionally specify `player_color` to
        start managing that color
        """

        key_w, key_b = [uuid4().hex[-KEY_LEN:] for _ in range(2)]
        keys = {Color.white: key_w, Color.black: key_b}

        try:
            await self._connection.execute(
                """
                CALL new_game($1, $2, $3, $4, $5)
                """,
                pickle.dumps(game),
                key_w,
                key_b,
                player_color.name if player_color else None,
                self._machine_id,
            )

        except Exception as e:
            logging.error(
                f"Encountered exception while attempting to write new game: {e}"
            )
            return False, None

        else:
            logging.info(f"Successfully wrote new game with keys {keys} to database")

            if player_color:
                # TODO: these can probably be reasonably combined
                # TODO: use real callbacks
                await self._subscribe_to_game_status(keys[player_color], None)
                await self._subcribe_to_chat_feed(keys[player_color], None)

            return True, keys

    async def join_game(self, player_key: str) -> Optional[JoinResult]:
        """
        Attempt to join a game using `player_key` and return the result of the
        operation or None if an exception occurs
        """

        try:
            async with self._connection.transaction():
                res = await self._connection.fetchrow(
                    """
                    SELECT * from join_game($1, $2);
                    """,
                    player_key,
                    self._machine_id,
                )

        except Exception as e:
            logging.error(
                "Encountered exception while attempting to join game with key"
                f" {player_key}: {e}"
            )
            return None

        else:
            logging.info(f"Attempt to join game with key {player_key} returned '{res}'")

            res = JoinResult[res]
            if res is JoinResult.success:
                # TODO: use real callbacks
                await self._subscribe_to_game_status(player_key, None)
                await self._subcribe_to_chat_feed(player_key, None)
                # TODO: need to read in game status and chat feed. one (somewhat
                # inefficient) way would be to simply issue a notification on
                # the channels we are now listening on

            return res

    async def _subscribe_to_game_status(
        self, player_key: str, update_callback: Callable[[Game], None]
    ) -> None:
        """
        Subscribe to the game status channel corresponding to `player_key` and
        register `update_callback` to receive game status updates. Should be
        called only after successfully creating or joining a game
        """

        def listener_callback(*_):
            self._update_queue.put_nowait(
                (_UpdateType.game_status, player_key, update_callback)
            )

        try:
            await self._connection.add_listener(
                f"game_status_{player_key}", listener_callback
            )

        except Exception as e:
            logging.error(
                "Encountered exception when subscribing to game status updates for"
                f" player key {player_key}"
            )

    async def _update_consumer(self) -> None:
        """
        The top-level consumer for queued updates. Routes to type-specific
        consumers
        """

        while True:
            update_type: _UpdateType
            player_key: str
            callback: Callable[[Any], None]
            update_type, player_key, callback = await self._update_queue.get()

            if update_type is _UpdateType.game_status:
                await self._game_status_consumer(player_key, callback)
            elif update_type is _UpdateType.chat:
                await self._chat_consumer(player_key, callback)
            else:
                logging.error(f"Found unknown update type {update_type} in queue")

            # NOTE: as we aren't attempting to join the queue in the current
            # design, this call doesn't really do anything useful. that said,
            # it's good practice, because it future-proofs us should we have a
            # reason to join the queue later on
            self._update_queue.task_done()

    async def _game_status_consumer(
        self, player_key: str, callback: Callable[[Game], None]
    ) -> None:
        # TODO: stub. need to go to db for latest version and invoke callback
        # with the result
        print(f"In game status consumer with key {player_key}")

    async def _subcribe_to_chat_feed(
        # TODO: what is update_callback's signature?
        self,
        player_key: int,
        update_callback: Callable[[Any], None],
    ) -> None:
        """
        Subscribe to the chat feed channel corresponding to `player_key` and
        register a callback to receive chat feed updates. Should be called only
        after successfully creating or joining a game
        """

        def listener_callback(*_):
            self._update_queue.put_nowait(
                (_UpdateType.chat, player_key, update_callback)
            )

        try:
            await self._connection.add_listener(f"chat_{player_key}", listener_callback)

        except Exception as e:
            logging.error(
                "Encountered exception when subscribing to chat updates for"
                f" player key {player_key}"
            )

    async def _chat_consumer(
        self, player_key: str, callback: Callable[[ChatMessage], None]
    ) -> None:
        # TODO: stub. need to go to db for updates since last known id and
        # invoke callback with the result
        print(f"In chat consumer with key {player_key}")

    async def write_game(self, player_key: str, game: Game) -> bool:
        """
        Attempt to write `game` and increment its version in the database.
        Return True on success and False on failure, i.e. when the write has
        been preempted from another source
        """

        version = game.version()
        log_text = f"game for player key {player_key} to version {version}"

        try:
            async with self._connection.transaction():
                res = await self._connection.fetchval(
                    """
                    SELECT * from write_game($1, $2, $3)
                    """,
                    player_key,
                    pickle.dumps(game),
                    version,
                )

        except Exception as e:
            logging.error(f"Encountered exception attempting to update {log_text}: {e}")
            return False

        else:
            if res:
                logging.info(f"Successfully updated {log_text}")
            else:
                logging.info(f"Preempted attempting to update {log_text}")
            return res

    async def write_chat(self, player_key: str, message: ChatMessage) -> bool:
        """
        Attempt to write `message` to the database. Return True on success and
        False otherwise (unspecified network or database failure)
        """

        try:
            async with self._connection.transaction():
                res = await self._connection.fetchval(
                    """
                    SELECT * FROM write_chat($1, $2, $3);
                    """,
                    message.timestamp,
                    message.message,
                    player_key,
                )

        except Exception as e:
            logging.error(
                f"Encountered exception while attempting to write chat message {message}: {e}"
            )
            return False

        else:
            if res:
                logging.info(f"Successfully wrote chat message {message}")
            else:
                logging.warn(
                    f"When attempting to write chat message {message} from player key"
                    f" {player_key}, a game associated with that key could not be found"
                )
            return res

    async def unsubscribe(self, player_key: str) -> bool:
        """
        Attempt to unsubscribe from channels associated with `player_key` and
        modify the row in the `player_key` table appropriately. Return True on
        success and False otherwise
        """

        try:
            async with self._connection.transaction():
                res = await self._connection.fetchval(
                    """
                    SELECT * FROM unsubscribe($1, $2);
                    """,
                    player_key,
                    self._machine_id,
                )

        except Exception as e:
            logging.error(
                "Encountered exception while unsubscribing from player key"
                f" {player_key}: {e}"
            )
            return False

        else:
            if res:
                logging.info(f"Successfully unsubscribed player key {player_key}")
            else:
                logging.warn(
                    f"When unsubscribing from player key {player_key}, no record was"
                    " found of a connected player managed by this game server"
                )
            return res

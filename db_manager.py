from collections import defaultdict
from enum import Enum, auto
from constants import KEY_LEN
from game import ChatMessage, Color, Game
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Tuple
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
    opponent_connected = auto()


@asyncinit
class DbManager:
    __slots__ = ("_connection", "_machine_id", "_update_queue", "_listening_channels")

    async def __init__(
        self,
        dsn: str = "postgres://randy@localhost/randy",
        do_setup: bool = False,
    ) -> None:
        """
        Interface to the postgres database store. Responsibilities include:

        - On start up, cleaning the player key table in case of reboot while
          managing any connections
        - Handling new game creation
        - Handling joining a connected player to an existing game
        - Subscribing to and registering callbacks for various update channels
        - Issuing game updates to the database and reporting success or failure
        - Issuing chat messages to the database
        - Unsubscribing from update channels and cleaning up

        :param str dsn: data source name url

        :param bool do_setup: if True, run all table/index/function/etc.
        creation scripts as if using a fresh database. useful for testing
        """

        # TODO: we probably want to use a connection pool instead of a single
        # connection. look into best practices
        self._connection: asyncpg.connection.Connection = await asyncpg.connect(dsn)

        # { player_key: [(channel, callback), ...], ...}
        # populate whenever adding listeners and lookup/delete record when
        # unlistening
        #
        # TODO: if multiple listener connections are used, the connection
        # associated with each channel will also need to be stored. this will
        # also be useful for handling reconnect logic (db restart, etc.)
        self._listening_channels: DefaultDict[
            str, List[Tuple[str, Callable]]
        ] = defaultdict(list)

        # machine-id is a reboot persistent unique identifier that should not be
        # shared externally. the following mimics sd_id128_get_machine_app_specific()
        with open("/etc/machine-id", "rb") as r:
            self._machine_id = sha256(r.readline().strip()).hexdigest()

        if do_setup:
            try:
                # NOTE: tables must be executed first. otherwise, it would be
                # sufficient to list the directory and execute each file
                for fn in ("tables", "indices", "views", "procedures", "functions"):
                    with open(f"./sql/{fn}.sql", "r") as r:
                        sql = r.read()
                    await self._connection.execute(sql)

            except Exception as e:
                logging.error(
                    f"Encountered exception while running db setup scripts: {e}"
                )
                raise e

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
    ) -> Optional[Dict[Color, str]]:
        """
        Attempt to write `game` to the database as a new game. Return a
        dictionary of Color: key pairs on success or None otherwise. Optionally
        specify `player_color` to start managing that color
        """

        key_w, key_b = [uuid4().hex[-KEY_LEN:] for _ in range(2)]
        keys = {Color.white: key_w, Color.black: key_b}

        try:
            async with self._connection.transaction():
                await self._connection.execute(
                    """
                    CALL new_game($1, $2, $3, $4, $5);
                    """,
                    pickle.dumps(game),
                    key_w,
                    key_b,
                    player_color.name if player_color else None,
                    self._machine_id,
                )
                if player_color:
                    # TODO: use real callbacks
                    await self._subscribe_to_updates(
                        keys[player_color], None, None, None
                    )

        except Exception as e:
            logging.error(
                f"Encountered exception while attempting to write new game: {e}"
            )
            return None

        else:
            logging.info(f"Successfully wrote new game with keys {keys} to database")
            return keys

    async def join_game(self, player_key: str) -> Optional[JoinResult]:
        """
        Attempt to join a game using `player_key` and return the result of the
        operation or None if an exception occurs
        """

        try:
            async with self._connection.transaction():
                res = await self._connection.fetchval(
                    """
                    SELECT * from join_game($1, $2);
                    """,
                    player_key,
                    self._machine_id,
                )
                res = JoinResult[res]
                if res is JoinResult.success:
                    # TODO: use real callbacks
                    await self._subscribe_to_updates(player_key, None, None, None)
                    await self._connection.execute(
                        """
                        CALL trigger_update_all($1);
                        """,
                        player_key,
                    )

        except Exception as e:
            logging.error(
                "Encountered exception while attempting to join game with key"
                f" {player_key}: {e}"
            )
            return None

        else:
            logging.info(
                f"Attempt to join game with key {player_key} returned '{res.name}'"
            )
            return res

    async def _subscribe_to_updates(
        self,
        player_key: str,
        game_callback: Callable[[str, Game], None],
        chat_callback: Callable[[str, List[ChatMessage]], None],
        opponent_connected_callback: Callable[[str, bool], None],
    ) -> None:
        """
        Subscribe to the update channels corresponding to `player_key` and
        register the provided callbacks to receive updates. Should be called
        only after successfully creating or joining a game
        """

        def listener_callback(
            update_type: _UpdateType, callback: Callable[[str, Any], None]
        ):
            return lambda _, _1, _2, payload: self._update_queue.put_nowait(
                (update_type, player_key, callback, payload)
            )

        try:
            for prefix, update_type, callback in (
                ("game_status_", _UpdateType.game_status, game_callback),
                ("chat_", _UpdateType.chat, chat_callback),
                (
                    "opponent_connected_",
                    _UpdateType.opponent_connected,
                    opponent_connected_callback,
                ),
            ):
                channel = f"{prefix}{player_key}"
                partial_callback = listener_callback(update_type, callback)
                await self._connection.add_listener(channel, partial_callback)
                self._listening_channels[player_key].append((channel, partial_callback))

        except Exception as e:
            logging.error(
                "Encountered exception when subscribing to status updates for"
                f" player key {player_key}: {e}"
            )
            raise e

        else:
            logging.info(f"Successfully subscribed to status updates for {player_key}")

    async def _update_consumer(self) -> None:
        """
        The top-level consumer for queued updates. Routes to type-specific
        consumers
        """

        while True:
            update_type: _UpdateType
            player_key: str
            callback: Callable[[str, Any], None]
            payload: str
            update_type, player_key, callback, payload = await self._update_queue.get()

            if update_type is _UpdateType.game_status:
                await self._game_status_consumer(player_key, callback)
            elif update_type is _UpdateType.chat:
                await self._chat_consumer(player_key, callback)
            elif update_type is _UpdateType.opponent_connected:
                await self._opponent_connected_consumer(player_key, callback, payload)
            else:
                logging.error(f"Found unknown update type {update_type} in queue")

            # NOTE: as we aren't attempting to join the queue in the current
            # design, this call doesn't really do anything useful. that said,
            # it's good practice, because it future-proofs us should we have a
            # reason to join the queue later on
            self._update_queue.task_done()

    async def _game_status_consumer(
        self, player_key: str, callback: Callable[[str, Game], None]
    ) -> None:
        # TODO: stub. need to go to db for latest version and invoke callback
        # with the result
        print(f"In game status consumer with key {player_key}")

    async def _chat_consumer(
        self, player_key: str, callback: Callable[[str, List[ChatMessage]], None]
    ) -> None:
        # TODO: stub. need to go to db for updates since last known id and
        # invoke callback with the result
        print(f"In chat consumer with key {player_key}")

    async def _opponent_connected_consumer(
        self, player_key: str, callback: Callable[[str, bool], None], payload: str
    ) -> None:
        # TODO: stub. if payload is not empty, use it, otherwise go to db for
        # status, and then invoke callback with the result
        print(
            f"In opponent connected consumer with key {player_key} and payload {payload}"
        )

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
                    SELECT * from write_game($1, $2, $3);
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
                if res:
                    for channel, callback in self._listening_channels[player_key]:
                        await self._connection.remove_listener(channel, callback)
                    del self._listening_channels[player_key]

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

import logging
from datetime import datetime
from chat import ChatMessage, ChatThread
import pickle
from typing import Dict
from game import Color, Game
from db_manager import DbManager, JoinResult, _UpdateType
import testing.postgresql
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class DbManagerTestCase(unittest.IsolatedAsyncioTestCase):
    """
    NOTE: there are a number of places in this suite where we need to wait a
    small amount of time for a listener to pick up a notify sent out as part of
    some action, and critically, since this is async code, we need to await
    *something* in order to yield control. to satisfy these demands, a short
    `await asyncio.sleep(0.1)` or the like is called. this doesn't really seem
    to be avoidable in order to test this functionality, but it's worth noting
    that timing-dependent tests are really fragile. if the test server is super
    busy, for example, maybe this isn't actually enough sleep time and the test
    intermittently fails. if a better solution presents itself, it should
    definitely be used.

    NOTE 2: for convenience, wherever we directly issue db queries in this
    suite, we use DbManager._listener_connection. In production, that connection
    is relegated to pub/sub only, and all other work is done using a connection
    pool
    """

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()

    async def asyncSetUp(self):
        self.game_status_callback = AsyncMock()
        self.chat_callback = AsyncMock()
        self.opponent_connected_callback = AsyncMock()
        self.manager: DbManager = await DbManager(
            self.game_status_callback,
            self.chat_callback,
            self.opponent_connected_callback,
            self.__class__.postgresql.url(),
            True,
        )

    async def asyncTearDown(self) -> None:
        await self.manager._listener_connection.close()
        await self.manager._connection_pool.close()

    async def test_startup_cleans_orphaned_rows(self):
        manager = self.manager
        keys: Dict[Color, str] = await manager.write_new_game(Game(), Color.white)
        self.assertEqual(
            keys[Color.white],
            await manager._listener_connection.fetchval(
                """
            SELECT key
            FROM player_key
            WHERE managed_by = $1
            """,
                manager._machine_id,
            ),
        )
        (
            players_connected,
            time_played,
            write_load_timestamp,
        ) = await manager._listener_connection.fetchrow(
            """
            SELECT players_connected, time_played, write_load_timestamp
            FROM game
            WHERE id = (
                SELECT game_id
                FROM player_key
                WHERE managed_by = $1
            )
            """,
            manager._machine_id,
        )
        self.assertEqual(players_connected, 1)
        self.assertEqual(time_played, 0)
        self.assertIsNotNone(write_load_timestamp)

        del manager
        manager: DbManager = await DbManager(
            self.game_status_callback,
            self.chat_callback,
            self.opponent_connected_callback,
            self.__class__.postgresql.url(),
            False,
        )
        # NOTE: it's important to fetch the row and not the value here, because
        # null being the expected type, fetchval conflates "returned a row with
        # a null value" and "didn't return any rows." we only want to succeed on
        # the former, so we fetch a full row and then get the value from it
        row = await manager._listener_connection.fetchrow(
            """
            SELECT managed_by
            FROM player_key
            WHERE key = $1
            """,
            keys[Color.white],
        )
        self.assertIsNone(row.get("managed_by"))
        (
            players_connected,
            _,
            write_load_timestamp,
        ) = await manager._listener_connection.fetchrow(
            """
            SELECT players_connected, time_played, write_load_timestamp
            FROM game
            WHERE id = (
                SELECT game_id
                FROM player_key
                WHERE key = $1
            )
            """,
            keys[Color.white],
        )
        self.assertEqual(players_connected, 0)
        self.assertIsNone(write_load_timestamp)

    async def test_write_new_game(self):
        manager = self.manager
        game = Game()
        keys: Dict[Color, str] = await manager.write_new_game(game, Color.white)

        row = await manager._listener_connection.fetchrow(
            """
            SELECT key, game_id, color, opponent_key
            FROM player_key
            WHERE managed_by = $1
            """,
            manager._machine_id,
        )
        game_id = row.get("game_id")
        self.assertEqual(keys[Color.white], row.get("key"))
        self.assertEqual(Color.white.name, row.get("color"))
        self.assertEqual(keys[Color.black], row.get("opponent_key"))

        row = await manager._listener_connection.fetchrow(
            """
            SELECT key, game_id, color, managed_by
            FROM player_key
            WHERE opponent_key = $1
            """,
            keys[Color.white],
        )
        self.assertEqual(keys[Color.black], row.get("key"))
        self.assertEqual(game_id, row.get("game_id"))
        self.assertEqual(Color.black.name, row.get("color"))
        self.assertIsNone(row.get("managed_by"))

        (
            game_data,
            time_played,
            version,
        ) = await manager._listener_connection.fetchrow(
            """
            SELECT *
            FROM get_game_status($1);
            """,
            keys[Color.white],
        )
        self.assertEqual(pickle.loads(game_data), game)
        self.assertEqual(game.version(), version)
        self.assertEqual(time_played, 0)

    async def test_join_game(self):
        manager = self.manager
        new_game_keys: Dict[Color, str] = await manager.write_new_game(
            Game(), Color.white
        )
        res: JoinResult
        res, keys = await manager.join_game("0000000000")
        self.assertEqual(res, JoinResult.dne)
        self.assertIsNone(keys)
        res, keys = await manager.join_game(new_game_keys[Color.white])
        self.assertEqual(res, JoinResult.in_use)
        self.assertIsNone(keys)
        res, keys = await manager.join_game(new_game_keys[Color.black])
        self.assertEqual(res, JoinResult.success)
        self.assertIsNotNone(keys)

        # see note on the suite class about timing-dependent tests
        await asyncio.sleep(0.1)
        self.opponent_connected_callback.assert_awaited_once()

    async def test_subscribe_to_updates(self):
        manager = self.manager
        key = "0123456789"
        await manager._subscribe_to_updates(key)
        self.assertEqual(len(manager._listening_channels[key]), len(_UpdateType))

    @patch("db_manager.pickle.dumps", MagicMock(return_value=b"1"))
    @patch("db_manager.pickle.loads", MagicMock(return_value=b"1"))
    async def test_write_game(self):
        """
        NOTE: pickling methods need to be mocked because of an error like

        _pickle.PicklingError: Can't pickle <class 'unittest.mock.MagicMock'>:
        it's not the same object as unittest.mock.MagicMock

        I think this might actually be something I can fix, i.e. something to do
        with the "Where to patch" trickiness with unittest mocking that isn't
        standing out to me, but I'm also not testing pickling functionality, so
        it doesn't really matter if they are real methods or not
        """

        manager = self.manager
        game = Game()
        keys: Dict[Color, str] = await manager.write_new_game(game, Color.white)

        # this should not work because the game version is still 0
        self.assertIsNone(await manager.write_game(keys[Color.white], game))

        # neither should this, because the version is too high
        with patch.object(Game, "version", return_value=2):
            self.assertIsNone(await manager.write_game(keys[Color.white], game))

        # this is just right. we also want to make sure game status was fired,
        # so subscribe to the opponent key
        await manager._subscribe_to_updates(keys[Color.black])
        with patch.object(Game, "version", return_value=1):
            self.assertGreater(await manager.write_game(keys[Color.white], game), 0)
        # see note on the suite class about timing-dependent tests
        await asyncio.sleep(0.1)
        self.game_status_callback.assert_awaited_once()

    async def test_write_chat(self):
        manager = self.manager
        timestamp = datetime.now().timestamp()
        msg_text = "hi bob"
        keys: Dict[Color, str] = await manager.write_new_game(Game(), Color.white)
        message = ChatMessage(timestamp, Color.white, msg_text)

        self.assertTrue(await manager.write_chat(keys[Color.white], message))
        message.id = 1
        thread = ChatThread([message])
        # see note on the suite class about timing-dependent tests
        await asyncio.sleep(0.1)
        self.chat_callback.assert_awaited_once_with(keys[Color.white], thread)

        # make sure that both players receive updates
        await manager._subscribe_to_updates(keys[Color.black])
        self.assertTrue(await manager.write_chat(keys[Color.black], message))
        await asyncio.sleep(0.1)
        # once for the first message, twice for the second after having subbed
        # to the other player's updates
        self.assertEqual(self.chat_callback.await_count, 3)

    async def test_unsubscribe(self):
        manager = self.manager
        keys: Dict[Color, str] = await manager.write_new_game(Game(), Color.white)
        self.assertEqual(len(manager._listening_channels[keys[Color.white]]), 3)
        self.assertFalse(await manager.unsubscribe(keys[Color.black]))
        self.assertTrue(await manager.unsubscribe(keys[Color.white]))
        self.assertEqual(len(manager._listening_channels[keys[Color.white]]), 0)

    async def test_trigger_update_all(self):
        manager = self.manager
        game = Game(1)
        keys: Dict[Color, str] = await manager.write_new_game(game, Color.white)
        await manager.trigger_update_all(keys[Color.white])
        # see note on the suite class about timing-dependent tests
        await asyncio.sleep(0.1)
        self.game_status_callback.assert_awaited_once_with(keys[Color.white], game, 0.0)
        self.chat_callback.assert_awaited_once_with(
            keys[Color.white], ChatThread(is_complete=True)
        )
        self.opponent_connected_callback.assert_awaited_once_with(
            keys[Color.white], False
        )

    @patch.object(DbManager, "trigger_update_all")
    async def test_db_reconnect(self, trigger_update_all_mock: AsyncMock):
        manager = self.manager
        keys: Dict[Color, str] = await manager.write_new_game(Game(), Color.white)
        # losing the db connection logs a bunch of errors, which just clutters
        # the test output. note that 50 is CRITICAL per
        # https://docs.python.org/3/howto/logging.html#logging-levels, so this
        # disables all logging
        logging.disable(50)
        # terminate, *not* stop, which also cleans up the tmp file that
        # testing.postgresql uses, rendering it unable to be restarted
        self.__class__.postgresql.terminate()
        # it might seem like asserting that the connection is closed here would
        # be a good idea, but since it gets released back to the pool, this
        # isn't possible in a straightforward way. that a connection closes when
        # the server terminates isn't testing any of our project code anyways,
        # so the assertions below are sufficient
        self.__class__.postgresql.start()
        # see note on the suite class about timing-dependent tests
        await asyncio.sleep(0.1)
        self.assertFalse(manager._listener_connection.is_closed())
        trigger_update_all_mock.assert_awaited_once_with(keys[Color.white])

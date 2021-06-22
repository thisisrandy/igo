import pickle
from typing import Dict
from game import Color, Game
from db_manager import DbManager, JoinResult
import testing.postgresql
import unittest
from unittest.mock import AsyncMock


class DbManagerTestCase(unittest.IsolatedAsyncioTestCase):
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

    async def test_startup_cleans_orphaned_rows(self):
        manager = self.manager
        keys: Dict[Color, str] = await manager.write_new_game(Game(), Color.white)
        self.assertEqual(
            keys[Color.white],
            await manager._connection.fetchval(
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
        ) = await manager._connection.fetchrow(
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
        row = await manager._connection.fetchrow(
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
        ) = await manager._connection.fetchrow(
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

        row = await manager._connection.fetchrow(
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

        row = await manager._connection.fetchrow(
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

        (game_data, time_played, version,) = await manager._connection.fetchrow(
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
        keys: Dict[Color, str] = await manager.write_new_game(Game(), Color.white)
        res: JoinResult
        res, _ = await manager.join_game("0000000000")
        self.assertEqual(res, JoinResult.dne)
        res, _ = await manager.join_game(keys[Color.white])
        self.assertEqual(res, JoinResult.in_use)
        res, _ = await manager.join_game(keys[Color.black])
        self.assertEqual(res, JoinResult.success)
        pass

    async def test_subscribe_to_updates(self):
        # TODO: stub
        pass

    async def test_write_game(self):
        # TODO: stub
        pass

    async def test_write_chat(self):
        # TODO: stub
        pass

    async def test_unsubscribe(self):
        # TODO: stub
        pass

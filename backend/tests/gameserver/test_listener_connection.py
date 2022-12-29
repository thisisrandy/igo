import unittest
from unittest.mock import MagicMock
import asyncpg
import testing.postgresql


class ListenConnectionTestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()

    async def asyncSetUp(self):
        self.connection: asyncpg.connection.Connection = await asyncpg.connect(
            self.__class__.postgresql.url()
        )

    async def asyncTearDown(self) -> None:
        await self.connection.close()

    async def test_simultaneous_notifies(self):
        # this is a test to confirm that one connection can handle listening to
        # an arbitrary number of connections. crank num_channels up to 10000 or
        # so for proof (takes ~15 seconds). turned down so that discover test
        # runs don't take forever
        num_channels = 10
        callback = MagicMock()
        for i in range(num_channels):
            await self.connection.add_listener(f"channel_{i}", callback)
        async with self.connection.transaction():
            for i in range(num_channels):
                await self.connection.execute(f"NOTIFY channel_{i}")
        self.assertEqual(callback.call_count, num_channels)

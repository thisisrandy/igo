from containers import GameStatusContainer
from db_manager import DbManager
import unittest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from tornado.websocket import WebSocketHandler
from game_manager import GameStore, GameManager
import json
from messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessageType,
)
from game import Color, ActionType, Game
from constants import TYPE, VS, COLOR, SIZE, KOMI, KEY, ACTION_TYPE, COORDS, MESSAGE
import testing.postgresql


@patch.object(WebSocketHandler, "__init__", lambda self: None)
@patch.object(WebSocketHandler, "__hash__", lambda self: 1)
@patch.object(WebSocketHandler, "__eq__", lambda self, o: o is self)
class GameManagerUnitTestCase(unittest.IsolatedAsyncioTestCase):
    """
    Mock GameStore and just test that GameManager routes things to the correct
    methods
    """

    async def asyncSetUp(self):
        # NOTE: although DbManager.__init__ is async, unittest.mock doesn't seem
        # to entirely understand what the @asyncinit decorator is doing, so it
        # wants a synchronous mock instead
        self.db_manager_mock = MagicMock(return_value=object())
        self.dsn = "postgres://foo@bar/baz"
        with patch.object(DbManager, "__init__", self.db_manager_mock):
            self.gm: GameManager = await GameManager(self.dsn)

    def test_init(self):
        # test that db manager created with correct url
        self.db_manager_mock.assert_called_once()
        self.assertEqual(self.db_manager_mock.call_args.args[3], self.dsn)

    @patch.object(GameStore, "unsubscribe")
    async def test_unsubscribe(self, unsubscribe: Mock):
        # test that store's unsubscribe is called
        player = WebSocketHandler()
        await self.gm.unsubscribe(player)
        unsubscribe.assert_called_once_with(player)

    @patch.object(GameStore, "new_game")
    @patch.object(GameStore, "join_game")
    @patch.object(GameStore, "route_message")
    async def test_route_message(
        self, route_message: Mock, join_game: Mock, new_game: Mock
    ):
        # test that correct store methods are called for each message type
        player = WebSocketHandler()
        key = "0123456789"

        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.new_game.name,
                    VS: "human",
                    COLOR: Color.white.name,
                    SIZE: 19,
                    KOMI: 6.5,
                }
            ),
            player,
        )
        await self.gm.route_message(msg)
        new_game.assert_called_once_with(msg)

        msg = IncomingMessage(
            json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key}),
            player,
        )
        await self.gm.route_message(msg)
        join_game.assert_called_once_with(msg)

        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.game_action.name,
                    KEY: key,
                    ACTION_TYPE: ActionType.place_stone.name,
                    COORDS: (0, 0),
                }
            ),
            player,
        )
        await self.gm.route_message(msg)
        route_message.assert_called_once_with(msg)

        route_message.call_count = 0  # so we can say "called once" below
        msg = IncomingMessage(
            json.dumps(
                {TYPE: IncomingMessageType.chat_message.name, KEY: key, MESSAGE: "hi"}
            ),
            player,
        )
        await self.gm.route_message(msg)
        route_message.assert_called_once_with(msg)


@patch.object(WebSocketHandler, "__init__", lambda self: None)
@patch.object(WebSocketHandler, "__hash__", lambda self: 1)
@patch.object(WebSocketHandler, "__eq__", lambda self, o: o is self)
class GameManagerIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    """
    Don't mock anything except for socket handlers and test the whole stack from
    GameManager down
    """

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()

    async def asyncSetUp(self):
        self.gm: GameManager = await GameManager(self.__class__.postgresql.url(), True)

    async def asyncTearDown(self) -> None:
        await self.gm.store._db_manager._connection.close()

    @patch("game_manager.send_outgoing_message")
    async def test_new_game(self, send_outgoing_message_mock: AsyncMock) -> None:
        player = WebSocketHandler()
        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.new_game.name,
                    VS: "human",
                    COLOR: Color.white.name,
                    SIZE: 19,
                    KOMI: 6.5,
                }
            ),
            player,
        )
        await self.gm.route_message(msg)
        self.assertEqual(send_outgoing_message_mock.await_count, 2)
        # response message
        await_args = send_outgoing_message_mock.await_args_list[0].args
        self.assertEqual(await_args[0], OutgoingMessageType.new_game_response)
        self.assertTrue(await_args[1].success)
        self.assertEqual(await_args[2], player)
        # game status message
        await_args = send_outgoing_message_mock.await_args_list[1].args
        self.assertEqual(await_args[0], OutgoingMessageType.game_status)
        self.assertTrue(isinstance(await_args[1], GameStatusContainer))
        self.assertEqual(await_args[2], player)

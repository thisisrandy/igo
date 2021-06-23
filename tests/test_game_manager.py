import asyncio
from chat import ChatThread
from typing import Dict, Tuple
from containers import (
    GameStatusContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
    OpponentConnectedContainer,
)
from db_manager import DbManager
import unittest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from tornado.websocket import WebSocketHandler
from game_manager import ClientData, GameStore, GameManager
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

    async def createNewGame(self) -> Tuple[WebSocketHandler, ClientData]:
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
        return player, self.gm.store._clients[player]

    async def asyncTearDown(self) -> None:
        await self.gm.store._db_manager._connection.close()

    @patch("game_manager.send_outgoing_message")
    async def test_new_game(self, send_outgoing_message_mock: AsyncMock) -> None:
        player, _ = await self.createNewGame()
        self.assertEqual(send_outgoing_message_mock.await_count, 2)
        # response message
        await_args = send_outgoing_message_mock.await_args_list[0].args
        self.assertEqual(await_args[0], OutgoingMessageType.new_game_response)
        self.assertTrue(await_args[1].success)
        self.assertEqual(await_args[2], player)
        # game status message
        await_args = send_outgoing_message_mock.await_args_list[1].args
        self.assertEqual(await_args[0], OutgoingMessageType.game_status)
        self.assertIsInstance(await_args[1], GameStatusContainer)
        self.assertEqual(await_args[2], player)

    @patch("game_manager.send_outgoing_message")
    async def test_join_game(self, send_outgoing_message_mock: AsyncMock) -> None:
        player: WebSocketHandler
        client_data: ClientData
        player, client_data = await self.createNewGame()
        new_game_response: NewGameResponseContainer = (
            send_outgoing_message_mock.await_args_list[0].args[1]
        )
        self.assertIsInstance(new_game_response, NewGameResponseContainer)
        keys: Dict[Color, str] = new_game_response.keys

        # already playing
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.white]}
                ),
                player,
            )
        )
        response: JoinGameResponseContainer = (
            send_outgoing_message_mock.await_args_list[-1].args[1]
        )
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("already playing" in response.explanation)

        # bad key
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: "0000000000"}
                ),
                player,
            )
        )
        response: JoinGameResponseContainer = (
            send_outgoing_message_mock.await_args_list[-1].args[1]
        )
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("not found" in response.explanation)

        # someone else playing
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.white]}
                ),
                WebSocketHandler(),
            )
        )
        response: JoinGameResponseContainer = (
            send_outgoing_message_mock.await_args_list[-1].args[1]
        )
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("Someone else" in response.explanation)

        # success, including unsub
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.black]}
                ),
                player,
            )
        )
        # see note in test_db_manager about timing-dependent tests
        await asyncio.sleep(0.1)
        # receive join response first
        response: JoinGameResponseContainer = (
            send_outgoing_message_mock.await_args_list[-5].args[1]
        )
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertTrue(response.success)
        self.assertTrue(
            f"joined the game as {Color.black.name}" in response.explanation
        )
        # unsub to old key triggers opponent not connected on the new key
        # channel. a bit quirky, but practically inconsequential
        self_unsubbed: OpponentConnectedContainer = (
            send_outgoing_message_mock.await_args_list[-4].args[1]
        )
        self.assertIsInstance(self_unsubbed, OpponentConnectedContainer)
        self.assertFalse(self_unsubbed.opponent_connected)
        # now trigger update all hits us with game status, chat, and opponent
        # connected from the database in sequence
        trigger_game_status: GameStatusContainer = (
            send_outgoing_message_mock.await_args_list[-3].args[1]
        )
        self.assertIsInstance(trigger_game_status, GameStatusContainer)
        self.assertEqual(trigger_game_status.game, client_data.game)
        trigger_chat: ChatThread = send_outgoing_message_mock.await_args_list[-2].args[
            1
        ]
        self.assertIsInstance(trigger_chat, ChatThread)
        self.assertEqual(trigger_chat, client_data.chat_thread)
        trigger_opp_connd: OpponentConnectedContainer = (
            send_outgoing_message_mock.await_args_list[-1].args[1]
        )
        self.assertIsInstance(trigger_opp_connd, OpponentConnectedContainer)
        self.assertFalse(trigger_opp_connd.opponent_connected)

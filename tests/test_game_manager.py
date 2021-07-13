import asyncio
from igo.gameserver.chat import ChatThread
from typing import Dict, Optional, Tuple
from igo.gameserver.containers import (
    ActionResponseContainer,
    GameStatusContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
    OpponentConnectedContainer,
)
from igo.gameserver.db_manager import DbManager
import unittest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from tornado.websocket import WebSocketHandler
from igo.gameserver.game_manager import ClientData, GameStore, GameManager
import json
from igo.gameserver.messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessage,
    OutgoingMessageType,
)
from igo.game import Color, ActionType, Game
from igo.gameserver.constants import (
    TYPE,
    VS,
    COLOR,
    SIZE,
    KOMI,
    KEY,
    ACTION_TYPE,
    COORDS,
    MESSAGE,
)
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
        await self.gm.store._db_manager._listener_connection.close()
        await self.gm.store._db_manager._connection_pool.close()

    async def createNewGame(
        self, player: Optional[WebSocketHandler] = None
    ) -> Tuple[WebSocketHandler, ClientData]:
        """
        Create new game and join as white. Optionally provider the client
        handler and return the client handler and internal data from the store
        """

        if player is None:
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

    @patch.object(OutgoingMessage, "__init__")
    @patch.object(OutgoingMessage, "send")
    async def test_new_game(self, send_mock: AsyncMock, init_mock: Mock) -> None:
        init_mock.return_value = None
        player, _ = await self.createNewGame()
        self.assertEqual(send_mock.await_count, 4)
        # response message
        init_args = init_mock.call_args_list[0].args
        self.assertEqual(init_args[0], OutgoingMessageType.new_game_response)
        self.assertTrue(init_args[1].success)
        self.assertEqual(init_args[2], player)
        # game status message
        init_args = init_mock.call_args_list[1].args
        self.assertEqual(init_args[0], OutgoingMessageType.game_status)
        self.assertIsInstance(init_args[1], GameStatusContainer)
        self.assertEqual(init_args[2], player)
        # chat
        init_args = init_mock.call_args_list[2].args
        self.assertEqual(init_args[0], OutgoingMessageType.chat)
        self.assertIsInstance(init_args[1], ChatThread)
        self.assertEqual(init_args[2], player)
        # opponent connected
        init_args = init_mock.call_args_list[3].args
        self.assertEqual(init_args[0], OutgoingMessageType.opponent_connected)
        self.assertIsInstance(init_args[1], OpponentConnectedContainer)
        self.assertEqual(init_args[2], player)
        # create another new game while still subscribed to the old one. there's
        # no signal that gets sent back out for us to test that we were
        # unsubscribed from the old game, and it isn't appropriate to dig into
        # the internal state of the store/db too much in an integration test,
        # but we can at least make sure that it succeeds and four more messages
        # are sent
        await self.createNewGame(player)
        self.assertEqual(send_mock.await_count, 8)

    @patch.object(OutgoingMessage, "__init__")
    @patch.object(OutgoingMessage, "send")
    async def test_join_game(self, send_mock: AsyncMock, init_mock: Mock) -> None:
        init_mock.return_value = None
        player: WebSocketHandler
        client_data: ClientData
        player, client_data = await self.createNewGame()
        new_game_response: NewGameResponseContainer = init_mock.call_args_list[0].args[
            1
        ]
        self.assertIsInstance(new_game_response, NewGameResponseContainer)
        keys: Dict[Color, str] = new_game_response.keys

        # reset ahead of all incoming messages
        send_mock.call_count = 0
        # already playing
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.white]}
                ),
                player,
            )
        )
        self.assertEqual(send_mock.call_count, 1)
        response: JoinGameResponseContainer = init_mock.call_args_list[-1].args[1]
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("already playing" in response.explanation)

        # bad key
        send_mock.call_count = 0
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: "0000000000"}
                ),
                player,
            )
        )
        self.assertEqual(send_mock.call_count, 1)
        response: JoinGameResponseContainer = init_mock.call_args_list[-1].args[1]
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("not found" in response.explanation)

        # someone else playing
        send_mock.call_count = 0
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.white]}
                ),
                WebSocketHandler(),
            )
        )
        self.assertEqual(send_mock.call_count, 1)
        response: JoinGameResponseContainer = init_mock.call_args_list[-1].args[1]
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("Someone else" in response.explanation)

        # success, including unsub
        send_mock.call_count = 0
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
        # when we join using the second player key, triggering a notification on
        # its opponent connected channel, we are still subscribed to the old
        # key's channel. ideally, join/unsub/unlisten would all be
        # transactional, but the design of the db_manager is such that there is
        # a dedicated pub/sub connection alongside a pool that's used for
        # everything else, so we can't make the whole sequence of operations
        # transactional without a complicated two stage ("distributed") commit.
        # as this is the only known consequence of not bundling in the
        # unlistens, and as it is practically inconsequential, it seems
        # reasonable to just let it slip through. we test for it here to record
        # and explain the behavior
        self.assertEqual(send_mock.call_count, 5)
        self_subbed: OpponentConnectedContainer = init_mock.call_args_list[-5].args[1]
        self.assertIsInstance(self_subbed, OpponentConnectedContainer)
        self.assertTrue(self_subbed.opponent_connected)
        # now starts the proper sequence. we receive the join response first
        response: JoinGameResponseContainer = init_mock.call_args_list[-4].args[1]
        self.assertIsInstance(response, JoinGameResponseContainer)
        self.assertTrue(response.success)
        self.assertTrue(
            f"joined the game as {Color.black.name}" in response.explanation
        )
        # now trigger update all hits us with game status, chat, and opponent
        # connected from the database in sequence
        trigger_game_status: GameStatusContainer = init_mock.call_args_list[-3].args[1]
        self.assertIsInstance(trigger_game_status, GameStatusContainer)
        self.assertEqual(trigger_game_status.game, client_data.game)
        trigger_chat: ChatThread = init_mock.call_args_list[-2].args[1]
        self.assertIsInstance(trigger_chat, ChatThread)
        self.assertEqual(trigger_chat, client_data.chat_thread)
        trigger_opp_connd: OpponentConnectedContainer = init_mock.call_args_list[
            -1
        ].args[1]
        self.assertIsInstance(trigger_opp_connd, OpponentConnectedContainer)
        self.assertFalse(trigger_opp_connd.opponent_connected)

    @patch.object(OutgoingMessage, "__init__")
    @patch.object(OutgoingMessage, "send")
    async def test_route_game_actions(
        self, send_mock: AsyncMock, init_mock: Mock
    ) -> None:
        init_mock.return_value = None
        p1: WebSocketHandler
        p1, _ = await self.createNewGame()
        new_game_response: NewGameResponseContainer = init_mock.call_args_list[0].args[
            1
        ]
        self.assertIsInstance(new_game_response, NewGameResponseContainer)
        keys: Dict[Color, str] = new_game_response.keys
        p2 = WebSocketHandler()
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.black]}
                ),
                p2,
            )
        )
        # see note in test_db_manager about timing-dependent tests. we're sleeping now
        # to let all of the new/join game messages get processed
        await asyncio.sleep(0.1)

        # reset before every route_message
        send_mock.call_count = 0
        # black goes first, so an initial move by white should fail
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: keys[Color.white],
                        ACTION_TYPE: ActionType.place_stone.name,
                        COORDS: [0, 0],
                    }
                ),
                p1,
            )
        )
        await asyncio.sleep(0.1)
        self.assertEqual(send_mock.call_count, 1)
        msg_type: OutgoingMessageType
        response: ActionResponseContainer
        msg_type, response, _ = init_mock.call_args_list[-1].args
        self.assertIsInstance(msg_type, OutgoingMessageType)
        self.assertIs(msg_type, OutgoingMessageType.game_action_response)
        self.assertIsInstance(response, ActionResponseContainer)
        self.assertFalse(response.success)
        self.assertTrue("isn't white's turn" in response.explanation)

        # initial move by black should succeed
        send_mock.call_count = 0
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: keys[Color.black],
                        ACTION_TYPE: ActionType.place_stone.name,
                        COORDS: [0, 0],
                    }
                ),
                p2,
            )
        )
        await asyncio.sleep(0.1)
        self.assertEqual(send_mock.call_count, 3)
        # game status should be sent to both players after the action response, so
        # check the last three messages
        msg_type, response, _ = init_mock.call_args_list[-3].args
        self.assertIs(msg_type, OutgoingMessageType.game_action_response)
        self.assertTrue(response.success)
        msg_type, _, _ = init_mock.call_args_list[-2].args
        self.assertIs(msg_type, OutgoingMessageType.game_status)
        msg_type, _, _ = init_mock.call_args_list[-1].args
        self.assertIs(msg_type, OutgoingMessageType.game_status)

        # NOTE: it doesn't seem to be possible to test action preemption without
        # artificially preventing the player being preempted from receiving an
        # update issued by the preempting action. the updates always go out
        # first when testing on a single machine. preemption is only actually
        # going to happen as a result of high database load or network delays

        # send a chat message
        send_mock.call_count = 0
        await self.gm.route_message(
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.chat_message.name,
                        KEY: keys[Color.black],
                        MESSAGE: "hi bob",
                    }
                ),
                p2,
            )
        )
        await asyncio.sleep(0.1)
        self.assertEqual(send_mock.call_count, 2)
        msg_type, _, _ = init_mock.call_args_list[-2].args
        self.assertIs(msg_type, OutgoingMessageType.chat)
        msg_type, _, _ = init_mock.call_args_list[-1].args
        self.assertIs(msg_type, OutgoingMessageType.chat)

        # finally, check that the sanity assertions fire
        with self.assertRaisesRegex(AssertionError, "unknown key"):
            await self.gm.route_message(
                IncomingMessage(
                    json.dumps(
                        {
                            TYPE: IncomingMessageType.game_action.name,
                            KEY: "0000000000",
                            ACTION_TYPE: ActionType.place_stone.name,
                            COORDS: [0, 0],
                        }
                    ),
                    p1,
                )
            )
        with self.assertRaisesRegex(
            AssertionError, "client who isn't subscribed to anything"
        ):
            await self.gm.route_message(
                IncomingMessage(
                    json.dumps(
                        {
                            TYPE: IncomingMessageType.game_action.name,
                            KEY: keys[Color.black],
                            ACTION_TYPE: ActionType.place_stone.name,
                            COORDS: [0, 0],
                        }
                    ),
                    WebSocketHandler(),
                )
            )
        with self.assertRaisesRegex(AssertionError, "isn't subscribed to that key"):
            await self.gm.route_message(
                IncomingMessage(
                    json.dumps(
                        {
                            TYPE: IncomingMessageType.game_action.name,
                            KEY: keys[Color.black],
                            ACTION_TYPE: ActionType.place_stone.name,
                            COORDS: [0, 0],
                        }
                    ),
                    p1,
                )
            )

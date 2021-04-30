from messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessageType,
)
import os
from uuid import uuid4
from game import ActionType, Color, Game
from game_manager import (
    ActionResponseContainer,
    GameContainer,
    GameManager,
    GameStore,
    JoinGameResponseContainer,
    NewGameResponseContainer,
)
import unittest
from unittest.mock import MagicMock, Mock, call, patch
import tempfile
from constants import ACTION_TYPE, COLOR, COORDS, KEY, KEY_LEN, TYPE, VS, KOMI
from tornado.websocket import WebSocketHandler
import json


class ResponseContainerTestCase(unittest.TestCase):
    def test_new_game(self):
        new_game = NewGameResponseContainer(
            True, "Success", {Color.white: "1234", Color.black: "5678"}, Color.white
        )
        self.assertEqual(
            new_game.jsonifyable(),
            {
                "success": True,
                "explanation": "Success",
                "keys": {"white": "1234", "black": "5678"},
                "your_color": Color.white.name,
            },
        )

    def test_join_game(self):
        join_game = JoinGameResponseContainer(
            True, "because", {Color.white: "1234", Color.black: "5678"}, Color.white
        )
        self.assertEqual(
            join_game.jsonifyable(),
            {
                "success": True,
                "explanation": "because",
                "keys": {"white": "1234", "black": "5678"},
                "your_color": Color.white.name,
            },
        )

    def test_action_response(self):
        action_response = ActionResponseContainer(False, "jesus made me do it")
        self.assertEqual(
            action_response.jsonifyable(),
            {"success": False, "explanation": "jesus made me do it"},
        )


@patch.object(WebSocketHandler, "__init__", lambda self: None)
class GameContainerTestCase(unittest.TestCase):
    def assertFileExists(self, path: str) -> None:
        if not os.path.isfile(path):
            raise AssertionError(f"File '{path}' does not exist")

    def assertFileDoesNotExists(self, path: str) -> None:
        if os.path.isfile(path):
            raise AssertionError(f"File '{path}' exists")

    def setUp(self) -> None:
        key_w, key_b = [uuid4().hex[-KEY_LEN:] for _ in range(2)]
        self.keys = {Color.white: key_w, Color.black: key_b}
        self.filepath = os.path.join(tempfile.mkdtemp(), f"{key_w}{key_b}")

    def tearDown(self) -> None:
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)

    def test_new_game(self):
        self.assertFileDoesNotExists(self.filepath)
        GameContainer(self.filepath, self.keys, Game(1))
        self.assertFileExists(self.filepath)

    def test_load_unload(self):
        gc = GameContainer(self.filepath, self.keys, Game(1))
        self.assertTrue(gc._is_loaded())
        board = gc.game.board
        gc.unload()
        self.assertFalse(gc._is_loaded())
        gc.load()
        # make sure nothing's changed
        self.assertEqual(gc.game.board, board)
        self.assertTrue(gc._is_loaded())

    def test_pass_message_assertions(self):
        gc = GameContainer(self.filepath, self.keys, Game(1))
        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.game_action.name,
                    KEY: self.keys[Color.white],
                    ACTION_TYPE: ActionType.place_stone.name,
                }
            ),
            WebSocketHandler(),
        )

        # test must be loaded
        gc.unload()
        with self.assertRaises(AssertionError):
            gc.pass_message(msg)
        gc.load()

        # test correct message type
        msg.message_type = IncomingMessageType.join_game
        with self.assertRaises(AssertionError):
            gc.pass_message(msg)

    @patch("game_manager.GameContainer._write")
    @patch("game_manager.send_outgoing_message")
    def test_pass_message(self, send_outgoing_message: Mock, _write: Mock):
        gc = GameContainer(self.filepath, self.keys, Game(1))
        # assert once here in order to assert unambiguously below that
        # pass_message will also call _write exactly once
        _write.assert_called_once()
        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.game_action.name,
                    KEY: self.keys[Color.white],
                    ACTION_TYPE: ActionType.request_draw.name,
                }
            ),
            WebSocketHandler(),
        )
        self.assertTrue(gc.pass_message(msg))
        self.assertEqual(_write.call_count, 2)
        send_outgoing_message.assert_called_once()
        self.assertIsNotNone(gc.game.pending_request)


@patch.object(WebSocketHandler, "__init__", lambda self: None)
@patch.object(WebSocketHandler, "__hash__", lambda self: 1)
@patch.object(WebSocketHandler, "__eq__", lambda self, o: o is self)
class GameStoreTestCase(unittest.TestCase):
    """NOTE: the object patches above allow us to parameterlessly create
    multiple WebSocketHandlers and use them as unique dictionary keys, which
    is how they are used in GameContainer's client attribute"""

    def set_up_game_container(self) -> str:
        key_w = "0123456789"
        key_b = "9876543210"
        dir = tempfile.mkdtemp()
        GameContainer(
            os.path.join(dir, f"{key_w}{key_b}"),
            {Color.white: key_w, Color.black: key_b},
            Game(3),
        ).unload()

        return key_w, key_b, dir

    def test_hydrate(self):
        # pickle a game, then start the store and make sure it's correctly
        # loaded
        key_w, key_b, dir = self.set_up_game_container()

        with patch.object(GameStore, "_hydrate_games") as _hydrate_games:
            GameStore(dir)
            _hydrate_games.assert_called_once()

        gs = GameStore(dir)
        self.assertIn(key_w, gs.keys)
        self.assertIn(key_b, gs.keys)
        self.assertEqual(len(gs.containers), 1)

    @patch("game_manager.send_outgoing_message")
    def test_send_game_status(self, send_outgoing_message: Mock):
        # subscribe two players and ensure status sent to both
        p1, p2 = WebSocketHandler(), WebSocketHandler()
        key_w, key_b, dir = self.set_up_game_container()
        gs = GameStore(dir)
        gc = gs.keys[key_w]

        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_w}),
                p1,
            )
        )
        send_outgoing_message.assert_called_with(
            OutgoingMessageType.game_status, gc.game, p1
        )

        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_b}),
                p2,
            )
        )
        # any_order=True because the ordering of a dictionary iterator isn't
        # defined, so we don't know which player was sent status first
        send_outgoing_message.assert_has_calls(
            [
                call(OutgoingMessageType.game_status, gc.game, p1),
                call(OutgoingMessageType.game_status, gc.game, p2),
            ],
            any_order=True,
        )

    @patch("game_manager.send_outgoing_message")
    def test_new_game(self, send_outgoing_message: Mock):
        # create a game, make sure the correct type of response was sent, the
        # game is loaded, and that the game status was subsequently sent via
        # mock
        player = WebSocketHandler()
        dir = tempfile.mkdtemp()
        gs = GameStore(dir)
        color = Color.white
        key_w, key_b = "0123456789", "9876543210"
        keys = {Color.white: key_w, Color.black: key_b}

        gs.new_game(
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.new_game.name,
                        VS: "human",
                        COLOR: color.name,
                        KOMI: 6.5,
                    }
                ),
                player,
            ),
            _keys=keys,
        )
        gc = next(iter(gs.containers))
        self.assertTrue(gc._is_loaded())
        send_outgoing_message.assert_has_calls(
            [
                call(
                    OutgoingMessageType.new_game_response,
                    NewGameResponseContainer(
                        True, "Successfully created new game", keys, color
                    ),
                    player,
                ),
                call(
                    OutgoingMessageType.game_status,
                    gc.game,
                    player,
                ),
            ]
        )

    @patch("game_manager.send_outgoing_message")
    def test_join_game(self, send_outgoing_message: Mock):
        p1, p2 = WebSocketHandler(), WebSocketHandler()
        key_w, key_b, dir = self.set_up_game_container()
        gs = GameStore(dir)
        gc = gs.keys[key_w]

        # join successfully and make sure message sent, game was loaded, and
        # the game status was subsequently sent via mock
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_w}),
                p1,
            )
        )
        self.assertTrue(gc._is_loaded())
        send_outgoing_message.assert_has_calls(
            [
                call(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        True,
                        "Successfully joined the game as white",
                        gc.keys,
                        Color.white,
                    ),
                    p1,
                ),
                call(OutgoingMessageType.game_status, gc.game, p1),
            ],
        )

        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_b}),
                p1,
            )
        )
        self.assertEqual(len(gs.subscriptions), 1)
        self.assertTrue(gc._is_loaded())
        send_outgoing_message.assert_has_calls(
            [
                call(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        True,
                        "Successfully joined the game as black",
                        gc.keys,
                        Color.black,
                    ),
                    p1,
                ),
                call(OutgoingMessageType.game_status, gc.game, p1),
            ],
        )

        # join unsuccessfully in various ways and make sure current message sent
        bad_key = "0000000000"
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: bad_key}),
                p2,
            )
        )
        send_outgoing_message.assert_called_with(
            OutgoingMessageType.join_game_response,
            JoinGameResponseContainer(
                False,
                (
                    f"A game corresponding to key {bad_key} was not found. Please"
                    " double-check and try again"
                ),
            ),
            p2,
        )
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_b}),
                p2,
            )
        )
        send_outgoing_message.assert_called_with(
            OutgoingMessageType.join_game_response,
            JoinGameResponseContainer(
                False,
                "Someone else is already playing that game and color",
            ),
            p2,
        )

        # finally, join the other player successfully
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_w}),
                p2,
            )
        )
        # any_order because status is also sent to p1 in unspecified order
        send_outgoing_message.assert_has_calls(
            [
                call(
                    OutgoingMessageType.join_game_response,
                    JoinGameResponseContainer(
                        True,
                        "Successfully joined the game as white",
                        gc.keys,
                        Color.white,
                    ),
                    p2,
                ),
                call(OutgoingMessageType.game_status, gc.game, p2),
            ],
            any_order=True,
        )

    @patch("game_manager.send_outgoing_message", lambda *args: None)
    def test_route_message(self):
        # mock out GameContainer to intercept pass_message. ensure that status
        # is sent via mock on success and not sent on failure
        player = WebSocketHandler()
        key_w, _, dir = self.set_up_game_container()
        gs = GameStore(dir)
        gc = gs.keys[key_w]

        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_w}),
                player,
            )
        )

        # success
        gs._send_game_status = MagicMock()
        gc.pass_message = MagicMock(return_value=True)
        gs.route_message(
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: key_w,
                        ACTION_TYPE: ActionType.place_stone.name,
                    }
                ),
                player,
            )
        )

        gc.pass_message.assert_called_once()
        gs._send_game_status.assert_called_once()

        # failure
        gs._send_game_status = MagicMock()
        gc.pass_message = MagicMock(return_value=False)
        gs.route_message(
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: key_w,
                        ACTION_TYPE: ActionType.place_stone.name,
                    }
                ),
                player,
            )
        )

        gc.pass_message.assert_called_once()
        gs._send_game_status.assert_not_called()

    @patch("game_manager.send_outgoing_message")
    def test_unsubscribe(self, _):
        # make sure num subscribers decreases and that game remains loaded if
        # remaining subscribers is 1 and is unloaded otherwise
        p1, p2 = WebSocketHandler(), WebSocketHandler()
        key_w, key_b, dir = self.set_up_game_container()
        gs = GameStore(dir)
        gc = gs.keys[key_w]

        # one player
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_w}),
                p1,
            )
        )
        self.assertTrue(gc._is_loaded())
        # no-op
        gs.unsubscribe(p2)
        self.assertTrue(gc._is_loaded())
        # real unsub
        gs.unsubscribe(p1)
        self.assertFalse(gc._is_loaded())

        # two players
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_w}),
                p1,
            )
        )
        gs.join_game(
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: key_b}),
                p2,
            )
        )
        self.assertTrue(gc._is_loaded())
        gs.unsubscribe(p1)
        self.assertTrue(gc._is_loaded())
        gs.unsubscribe(p2)
        self.assertFalse(gc._is_loaded())


@patch.object(WebSocketHandler, "__init__", lambda self: None)
@patch.object(WebSocketHandler, "__hash__", lambda self: 1)
@patch.object(WebSocketHandler, "__eq__", lambda self, o: o is self)
class GameManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        self.gm = GameManager(self.dir)

    def test_init(self):
        # test that store with correct dir is created
        self.assertEqual(self.gm.store.dir, self.dir)

    @patch.object(GameStore, "unsubscribe")
    def test_unsubscribe(self, unsubscribe: Mock):
        # test that store's unsubscribe is called
        player = WebSocketHandler()
        self.gm.unsubscribe(player)
        unsubscribe.assert_called_once_with(player)

    @patch.object(GameStore, "new_game")
    @patch.object(GameStore, "join_game")
    @patch.object(GameStore, "route_message")
    def test_route_message(self, route_message: Mock, join_game: Mock, new_game: Mock):
        # test that correct store methods are called for each message type
        player = WebSocketHandler()

        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.new_game.name,
                    VS: "human",
                    COLOR: Color.white.name,
                    KOMI: 6.5,
                }
            ),
            player,
        )
        self.gm.route_message(msg)
        new_game.assert_called_once_with(msg)

        msg = IncomingMessage(
            json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: "0123456789"}),
            player,
        )
        self.gm.route_message(msg)
        join_game.assert_called_once_with(msg)

        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.game_action.name,
                    KEY: "0123456789",
                    ACTION_TYPE: ActionType.place_stone.name,
                    COORDS: (0, 0),
                }
            ),
            player,
        )
        self.gm.route_message(msg)
        route_message.assert_called_once_with(msg)

from messages import IncomingMessage, IncomingMessageType
import os
from uuid import uuid4
from game import ActionType, Color, Game
from game_manager import (
    ActionResponseContainer,
    GameContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
)
import unittest
from unittest.mock import MagicMock, patch
import tempfile
from constants import ACTION_TYPE, COLOR, KEY, KEY_LEN, TYPE
from tornado.websocket import WebSocketHandler
import json


class ResponseContainerTestCase(unittest.TestCase):
    def test_new_game(self):
        new_game = NewGameResponseContainer(
            {Color.white: "1234", Color.black: "5678"}, Color.white
        )
        self.assertEqual(
            new_game.jsonifyable(),
            {
                "keys": {"white": "1234", "black": "5678"},
                "your_color": Color.white.name,
            },
        )

    def test_join_game(self):
        join_game = JoinGameResponseContainer(True, "because", Color.white)
        self.assertEqual(
            join_game.jsonifyable(),
            {"success": True, "explanation": "because", "your_color": Color.white.name},
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
                    KEY: "0123456789",
                    ACTION_TYPE: ActionType.place_stone.name,
                    COLOR: Color.white.name,
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
    @patch("messages.OutgoingMessage.send")
    def test_pass_message(self, send: MagicMock, _write: MagicMock):
        gc = GameContainer(self.filepath, self.keys, Game(1))
        # assert once here in order to assert unambiguously below that
        # pass_message will also call _write exactly once
        _write.assert_called_once()
        msg = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.game_action.name,
                    KEY: "0123456789",
                    ACTION_TYPE: ActionType.request_draw.name,
                    COLOR: Color.white.name,
                }
            ),
            WebSocketHandler(),
        )
        self.assertTrue(gc.pass_message(msg))
        self.assertEqual(_write.call_count, 2)
        send.assert_called_once()
        self.assertIsNotNone(gc.game.pending_request)


class GameStoreTestCase(unittest.TestCase):
    pass


class GameManagerTestCase(unittest.TestCase):
    pass
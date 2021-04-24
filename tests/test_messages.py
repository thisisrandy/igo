from game import ActionType, Color
from messages import IncomingMessage, IncomingMessageType
import unittest
from unittest.mock import patch
from tornado.websocket import WebSocketHandler
from constants import TYPE, VS, COLOR, KOMI, KEY, ACTION_TYPE
from json import dumps


@patch.object(WebSocketHandler, "__init__", lambda self: None)
class IncomingMessageTestCase(unittest.TestCase):
    def test_create_message(self):
        # test required keys (incorrect)
        with self.assertRaises(AssertionError):
            IncomingMessage(
                dumps({TYPE: IncomingMessageType.new_game.name}), WebSocketHandler()
            )
        with self.assertRaises(AssertionError):
            IncomingMessage(
                dumps({TYPE: IncomingMessageType.join_game.name}), WebSocketHandler()
            )
        with self.assertRaises(AssertionError):
            IncomingMessage(
                dumps({TYPE: IncomingMessageType.game_action.name}), WebSocketHandler()
            )

        # test required keys (correct)
        try:
            IncomingMessage(
                dumps(
                    {
                        TYPE: IncomingMessageType.new_game.name,
                        VS: "human",
                        COLOR: Color.white.name,
                        KOMI: 6.5,
                    }
                ),
                WebSocketHandler(),
            )
        except AssertionError as e:
            self.fail(
                f"Correctly specified IncomingMessage still failed required key assertion: {e}"
            )
        try:
            IncomingMessage(
                dumps({TYPE: IncomingMessageType.join_game.name, KEY: "0123456789"}),
                WebSocketHandler(),
            )
        except AssertionError:
            self.fail(
                f"Correctly specified IncomingMessage still failed required key assertion: {e}"
            )
        try:
            IncomingMessage(
                dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: "0123456789",
                        ACTION_TYPE: ActionType.place_stone.name,
                        COLOR: Color.white.name,
                    }
                ),
                WebSocketHandler(),
            )
        except AssertionError:
            self.fail(
                f"Correctly specified IncomingMessage still failed required key assertion: {e}"
            )


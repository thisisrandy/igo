from igo.gameserver.containers import GameStatusContainer
from datetime import datetime
from igo.game import ActionType, Color, Game
from igo.gameserver.messages import (
    IncomingMessage,
    IncomingMessageType,
    OutgoingMessage,
    OutgoingMessageType,
)
import unittest
from unittest.mock import AsyncMock, patch
from tornado.websocket import WebSocketHandler
from igo.gameserver.constants import SIZE, TYPE, VS, COLOR, KOMI, KEY, ACTION_TYPE
import json
import asyncio


@patch.object(WebSocketHandler, "__init__", lambda self: None)
@patch.object(WebSocketHandler, "__hash__", lambda self: 1)
@patch.object(WebSocketHandler, "__eq__", lambda self, o: o is self)
class IncomingMessageTestCase(unittest.TestCase):
    def test_create_message(self):
        # test required keys (incorrect)
        with self.assertRaises(AssertionError):
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.new_game.name}),
                WebSocketHandler(),
            )
        with self.assertRaises(AssertionError):
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.join_game.name}),
                WebSocketHandler(),
            )
        with self.assertRaises(AssertionError):
            IncomingMessage(
                json.dumps({TYPE: IncomingMessageType.game_action.name}),
                WebSocketHandler(),
            )

        # test required keys (correct)
        try:
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.new_game.name,
                        VS: "human",
                        COLOR: Color.white.name,
                        SIZE: 19,
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
                json.dumps(
                    {TYPE: IncomingMessageType.join_game.name, KEY: "0123456789"}
                ),
                WebSocketHandler(),
            )
        except AssertionError:
            self.fail(
                f"Correctly specified IncomingMessage still failed required key assertion: {e}"
            )
        try:
            IncomingMessage(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: "0123456789",
                        ACTION_TYPE: ActionType.place_stone.name,
                    }
                ),
                WebSocketHandler(),
            )
        except AssertionError:
            self.fail(
                f"Correctly specified IncomingMessage still failed required key assertion: {e}"
            )

    def test_eq(self):
        ts = datetime.now().timestamp()
        p1, p2 = WebSocketHandler(), WebSocketHandler()
        m1 = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.new_game.name,
                    VS: "human",
                    COLOR: Color.white.name,
                    SIZE: 19,
                    KOMI: 6.5,
                }
            ),
            p1,
        )
        m2 = IncomingMessage(
            json.dumps(
                {
                    TYPE: IncomingMessageType.new_game.name,
                    VS: "human",
                    COLOR: Color.white.name,
                    SIZE: 19,
                    KOMI: 6.5,
                }
            ),
            p1,
        )
        self.assertNotEqual(m1, m2)
        m1.timestamp = m2.timestamp = ts
        self.assertEqual(m1, m2)
        m2.websocket_handler = p2
        self.assertNotEqual(m1, m2)
        m2 = IncomingMessage(
            json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: "0123456789"}),
            p1,
        )
        m2.timestamp = ts
        self.assertNotEqual(m1, m2)


@patch.object(WebSocketHandler, "__init__", lambda self: None)
class OutgoingMessageTestCase(unittest.TestCase):
    def test_send(self):
        WebSocketHandler.write_message = AsyncMock(autospec=True)
        WebSocketHandler.id = "bob"
        g = GameStatusContainer(Game(1), 12.3)
        msg = OutgoingMessage(OutgoingMessageType.game_status, g, WebSocketHandler())
        asyncio.run(msg.send())
        WebSocketHandler.write_message.assert_called_once_with(
            json.dumps(msg.jsonifyable())
        )

    def test_jsonifyable(self):
        g = Game(1)
        msg_type = OutgoingMessageType.game_status
        self.assertEqual(
            {
                "messageType": msg_type.name,
                "data": g.jsonifyable(),
            },
            OutgoingMessage(msg_type, g).jsonifyable(),
        )

    def test_deserialize(self):
        msg = OutgoingMessage(
            OutgoingMessageType.game_status, GameStatusContainer(Game(1), 12.3)
        )
        self.assertEqual(OutgoingMessage.deserialize(msg.jsonifyable()), msg)

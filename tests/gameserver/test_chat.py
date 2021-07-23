from copy import deepcopy
from igo.gameserver.chat import ChatMessage, ChatThread
import unittest
from datetime import datetime
from igo.game import Color
from random import choice, uniform


class ChatMessageTestCase(unittest.TestCase):
    def test_jsonifyable(self):
        timestamp = datetime.now().timestamp()
        color = Color.white
        message = "hi bob"
        id = "123456"
        chat = ChatMessage(timestamp, color, message, id)
        self.assertEqual(
            chat.jsonifyable(),
            {
                "timestamp": timestamp,
                "color": color.name,
                "message": message,
                "id": id,
            },
        )

    def test_deserialize(self):
        chat = ChatMessage(datetime.now().timestamp(), Color.white, "hi bob", "123456")
        self.assertEqual(ChatMessage.deserialize(chat.jsonifyable()), chat)


class ChatThreadTestCase(unittest.TestCase):
    def setUp(self) -> None:
        unif = lambda: uniform(0.0, 100.0)
        self.thread = ChatThread(
            [
                ChatMessage(unif(), choice([c for c in Color]), str(unif()), i)
                for i in range(1, 11)
            ],
            True,
        )

    def test_jsonifyable(self):
        self.assertEqual(
            self.thread.jsonifyable(),
            {"thread": [msg.jsonifyable() for msg in self.thread], "isComplete": True},
        )

    def test_deserialize(self):
        self.assertEqual(ChatThread.deserialize(self.thread.jsonifyable()), self.thread)

    def test_get_after(self):
        self.assertEqual(len(self.thread), 10)
        self.assertEqual(len(self.thread.get_after(0)), 10)
        self.assertEqual(len(self.thread.get_after(5)), 5)
        self.assertEqual(len(self.thread.get_after(10)), 0)
        self.assertTrue(self.thread.get_after(0).is_complete)
        self.assertFalse(self.thread.get_after(1).is_complete)

    def test_append(self):
        t = deepcopy(self.thread)
        t.append(ChatMessage(0, Color.white, "hi bob", 20))
        self.assertEqual(len(t), 11)
        t = deepcopy(self.thread)
        t.append(*t.thread)
        self.assertEqual(len(t), 20)

    def test_extend(self):
        t = deepcopy(self.thread)
        t.extend(self.thread)
        self.assertEqual(len(t), 20)

from game import Color
from game_manager import (
    ActionResponseContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
)
import unittest


class ResponseContainerTestCase(unittest.TestCase):
    def test_new_game(self):
        new_game = NewGameResponseContainer({Color.white: "1234", Color.black: "5678"})
        self.assertEqual(new_game.jsonifyable(), {"white": "1234", "black": "5678"})

    def test_join_game(self):
        join_game = JoinGameResponseContainer(True, "because")
        self.assertEqual(
            join_game.jsonifyable(), {"success": True, "explanation": "because"}
        )

    def test_action_response(self):
        action_response = ActionResponseContainer(False, "jesus made me do it")
        self.assertEqual(
            action_response.jsonifyable(),
            {"success": False, "explanation": "jesus made me do it"},
        )


class GameContainerTestCase(unittest.TestCase):
    pass


class GameStoreTestCase(unittest.TestCase):
    pass


class GameManagerTestCase(unittest.TestCase):
    pass
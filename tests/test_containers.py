import unittest
from igo.gameserver.containers import (
    NewGameResponseContainer,
    JoinGameResponseContainer,
    ActionResponseContainer,
    OpponentConnectedContainer,
    GameStatusContainer,
)
from igo.game import Color, Game


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
                "yourColor": Color.white.name,
            },
        )
        self.assertEqual(
            NewGameResponseContainer.deserialize(new_game.jsonifyable()), new_game
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
                "yourColor": Color.white.name,
            },
        )
        self.assertEqual(
            JoinGameResponseContainer.deserialize(join_game.jsonifyable()), join_game
        )

    def test_action_response(self):
        action_response = ActionResponseContainer(False, "teh jesus made me do it")
        self.assertEqual(
            action_response.jsonifyable(),
            {"success": False, "explanation": "teh jesus made me do it"},
        )
        self.assertEqual(
            ActionResponseContainer.deserialize(action_response.jsonifyable()),
            action_response,
        )


class OpponentConnectedContainerTestCase(unittest.TestCase):
    def test_jsonifyable(self):
        opp_conned = OpponentConnectedContainer(True)
        self.assertEqual(opp_conned.jsonifyable(), {"opponentConnected": True})

    def test_deserialize(self):
        opp_conned = OpponentConnectedContainer(True)
        self.assertEqual(
            OpponentConnectedContainer.deserialize(opp_conned.jsonifyable()), opp_conned
        )


class GameStatusContainerTestCase(unittest.TestCase):
    def test_jsonifyable(self):
        game = Game()
        time_played = 123.12312
        game_status = GameStatusContainer(game, time_played)
        self.assertEqual(
            game_status.jsonifyable(), {**game.jsonifyable(), "timePlayed": time_played}
        )

    def test_deserialize(self):
        game_status = GameStatusContainer(Game(), 123.12312)
        self.assertEqual(
            GameStatusContainer.deserialize(game_status.jsonifyable()), game_status
        )

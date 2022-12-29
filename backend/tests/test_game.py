from datetime import datetime
from typing import Optional
from igo.game import (
    Action,
    ActionType,
    Board,
    Color,
    Game,
    GameStatus,
    Point,
    Request,
    RequestType,
    Result,
    ResultType,
)

import unittest


class RequestTestCase(unittest.TestCase):
    def test_deserialize(self):
        r = Request(RequestType.draw, Color.black)
        self.assertEqual(Request.deserialize(r.jsonifyable()), r)


class ResultTestCase(unittest.TestCase):
    def test_deserialize(self):
        r = Result(ResultType.standard_win, Color.black)
        self.assertEqual(Result.deserialize(r.jsonifyable()), r)


class PointTestCase(unittest.TestCase):
    def test_json(self):
        self.assertEqual(["", False, False, ""], Point().jsonifyable())
        self.assertEqual(["w", False, False, ""], Point(Color.white).jsonifyable())
        self.assertEqual(["b", False, False, ""], Point(Color.black).jsonifyable())
        self.assertEqual(["w", True, False, ""], Point(Color.white, True).jsonifyable())
        self.assertEqual(["b", True, False, ""], Point(Color.black, True).jsonifyable())
        self.assertEqual(
            ["b", False, True, ""], Point(Color.black, counted=True).jsonifyable()
        )
        self.assertEqual(
            ["", False, True, "b"],
            Point(counted=True, counts_for=Color.black).jsonifyable(),
        )

    def test_deserialize(self):
        p = Point()
        self.assertEqual(Point.deserialize(p.jsonifyable()), p)


class BoardTestCase(unittest.TestCase):
    def test_json(self):
        board = Board(3)
        self.assertEqual(
            board.jsonifyable(),
            {
                "size": 3,
                "points": [
                    [
                        ["", False, False, ""],
                        ["", False, False, ""],
                        ["", False, False, ""],
                    ],
                    [
                        ["", False, False, ""],
                        ["", False, False, ""],
                        ["", False, False, ""],
                    ],
                    [
                        ["", False, False, ""],
                        ["", False, False, ""],
                        ["", False, False, ""],
                    ],
                ],
            },
        )
        board[0][1].color = Color.black
        self.assertEqual(
            board.jsonifyable(),
            {
                "size": 3,
                "points": [
                    [
                        ["", False, False, ""],
                        ["b", False, False, ""],
                        ["", False, False, ""],
                    ],
                    [
                        ["", False, False, ""],
                        ["", False, False, ""],
                        ["", False, False, ""],
                    ],
                    [
                        ["", False, False, ""],
                        ["", False, False, ""],
                        ["", False, False, ""],
                    ],
                ],
            },
        )

    def test_eq(self):
        b1, b2, b3 = Board(3), Board(3), Board(5)
        self.assertEqual(b1, b2)
        self.assertNotEqual(b2, b3)
        b1[0][0].color = Color.black
        b2[0][0].color = Color.black
        self.assertEqual(b1, b2)
        b1[0][1].color = Color.white
        self.assertNotEqual(b1, b2)

    def test_deserialize(self):
        b = Board()
        self.assertEqual(Board.deserialize(b.jsonifyable()), b)


class GameTestCase(unittest.TestCase):
    def test_eq(self):
        g1, g2, g3 = Game(3), Game(3), Game(5)
        self.assertEqual(g1, g2)
        self.assertNotEqual(g1, g3)
        g1.take_action(
            Action(
                ActionType.place_stone, Color.black, datetime.now().timestamp(), (1, 1)
            )
        )
        self.assertNotEqual(g1, g2)

    def test_placement_assertions(self):
        g = Game(1)

        # no coords
        a = Action(ActionType.place_stone, Color.white, datetime.now().timestamp())
        with self.assertRaises(AssertionError):
            g.take_action(a)
        a.coords = (0, 0)

        # wrong status
        g.status = GameStatus.endgame
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.play

        # wrong type. Game.take_action should route this (correctly) to the
        # mark dead method, so we have to explicitly call the "private" method
        # to test the behavior
        a.action_type = ActionType.mark_dead
        with self.assertRaises(AssertionError):
            g._place_stone(a)

    def test_placement(self):
        g = Game(3)
        b = Board(3)
        success, _ = g.take_action(
            Action(
                ActionType.place_stone, Color.black, datetime.now().timestamp(), (0, 0)
            )
        )
        self.assertTrue(success)
        b[0][0].color = Color.black
        self.assertEqual(g.board, b)

    def test_turn(self):
        g = Game(3)
        success, msg = g.take_action(
            Action(
                ActionType.place_stone, Color.white, datetime.now().timestamp(), (0, 0)
            )
        )
        self.assertFalse(success)
        self.assertEqual(msg, "It isn't white's turn")
        g.take_action(
            Action(
                ActionType.place_stone, Color.black, datetime.now().timestamp(), (0, 0)
            )
        )
        success, msg = g.take_action(
            Action(
                ActionType.place_stone, Color.black, datetime.now().timestamp(), (0, 1)
            )
        )
        self.assertFalse(success)
        self.assertEqual(msg, "It isn't black's turn")

    def test_occupied(self):
        g = Game(3)
        g.take_action(
            Action(
                ActionType.place_stone, Color.black, datetime.now().timestamp(), (0, 0)
            )
        )
        success, msg = g.take_action(
            Action(
                ActionType.place_stone,
                Color.white,
                datetime.now().timestamp(),
                (0, 0),
            )
        )
        self.assertFalse(success)
        self.assertEqual(msg, "Point (0, 0) is occupied")

    def test_suicide(self):
        g = Game(3)
        ts = datetime.now().timestamp()
        actions = [
            Action(ActionType.place_stone, Color.black, ts, (1, 0)),
            Action(ActionType.place_stone, Color.white, ts, (0, 0)),
            Action(ActionType.place_stone, Color.black, ts, (1, 1)),
            Action(ActionType.place_stone, Color.white, ts, (0, 1)),
            Action(ActionType.place_stone, Color.black, ts, (1, 2)),
            Action(ActionType.place_stone, Color.white, ts, (0, 2)),
        ]
        for a in actions:
            success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "Playing at (0, 2) is suicide")

    def test_ko(self):
        g = Game(4)
        ts = datetime.now().timestamp()
        actions = [
            Action(ActionType.place_stone, Color.black, ts, (1, 0)),
            Action(ActionType.place_stone, Color.white, ts, (2, 0)),
            Action(ActionType.place_stone, Color.black, ts, (0, 1)),
            Action(ActionType.place_stone, Color.white, ts, (3, 1)),
            Action(ActionType.place_stone, Color.black, ts, (1, 2)),
            Action(ActionType.place_stone, Color.white, ts, (2, 2)),
            Action(ActionType.place_stone, Color.black, ts, (2, 1)),
            Action(ActionType.place_stone, Color.white, ts, (1, 1)),
            Action(ActionType.place_stone, Color.black, ts, (2, 1)),
        ]
        for a in actions:
            success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "Playing at (2, 1) violates the simple ko rule")

    def test_capture(self):
        g = Game(5)
        ts = datetime.now().timestamp()
        actions = [
            Action(ActionType.place_stone, Color.black, ts, (0, 0)),
            Action(ActionType.place_stone, Color.white, ts, (1, 0)),
            Action(ActionType.place_stone, Color.black, ts, (0, 1)),
            Action(ActionType.place_stone, Color.white, ts, (1, 1)),
            Action(ActionType.place_stone, Color.black, ts, (0, 2)),
            Action(ActionType.place_stone, Color.white, ts, (2, 2)),
            Action(ActionType.place_stone, Color.black, ts, (1, 2)),
            Action(ActionType.place_stone, Color.white, ts, (1, 3)),
            Action(ActionType.place_stone, Color.black, ts, (0, 3)),
            Action(ActionType.place_stone, Color.white, ts, (0, 4)),
        ]
        for a in actions:
            success, msg = g.take_action(a)
        self.assertEqual(len(g.action_stack), len(actions))
        self.assertEqual(g.prisoners[Color.black], 0)
        self.assertEqual(g.prisoners[Color.white], 5)

    def test_pass_assertions(self):
        g = Game(1)
        a = Action(ActionType.pass_turn, Color.white, datetime.now().timestamp())

        # wrong status
        g.status = GameStatus.endgame
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.play

        # wrong type. Game.take_action should route this (correctly) to the
        # mark dead method, so we have to explicitly call the "private" method
        # to test the behavior
        a.action_type = ActionType.mark_dead
        with self.assertRaises(AssertionError):
            g._pass_turn(a)

    def test_pass_turn(self):
        g = Game(1)
        ts = datetime.now().timestamp()
        success, msg = g.take_action(Action(ActionType.pass_turn, Color.black, ts))
        self.assertTrue(success)
        self.assertEqual(msg, "Black passed on their turn")
        self.assertTrue(g.turn is Color.white)
        self.assertTrue(g.status is GameStatus.play)
        success, msg = g.take_action(Action(ActionType.pass_turn, Color.white, ts))
        self.assertTrue(success)
        self.assertEqual(msg, "White passed on their turn")
        self.assertTrue(g.turn is Color.black)
        self.assertTrue(g.status is GameStatus.endgame)

    def test_resign_assertions(self):
        g = Game(1)
        a = Action(ActionType.resign, Color.black, datetime.now().timestamp())

        # wrong status
        g.status = GameStatus.endgame
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.play

        # wrong type. Game.take_action should route this (correctly) to the
        # mark dead method, so we have to explicitly call the "private" method
        # to test the behavior
        a.action_type = ActionType.mark_dead
        with self.assertRaises(AssertionError):
            g._resign(a)

    def test_resign(self):
        # test the basics
        g = Game(1)
        self.assertIsNone(g.result)
        a = Action(ActionType.resign, Color.black, datetime.now().timestamp())
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "Black resigned")
        self.assertEqual(g.status, GameStatus.complete)
        self.assertIsNotNone(g.result)
        self.assertEqual(g.result.result_type, ResultType.resignation)
        self.assertEqual(g.result.winner, Color.white)

        # test that white can resign on black's turn
        g = Game(1)
        a.color = Color.white
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "White resigned")

    def test_mark_dead_assertions(self):
        g = Game(1)

        # no coords
        a = Action(ActionType.mark_dead, Color.black, datetime.now().timestamp())
        with self.assertRaises(AssertionError):
            g.take_action(a)
        a.coords = (0, 0)

        # wrong status
        g.status = GameStatus.play
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.endgame

        # wrong type. Game.take_action should route this (correctly) to the
        # place stone method, so we have to explicitly call the "private"
        # method to test the behavior
        a.action_type = ActionType.place_stone
        with self.assertRaises(AssertionError):
            g._mark_dead(a)
        a.action_type = ActionType.mark_dead

        # already marked dead
        g.board[0][0].color = Color.white
        g.board[0][0].marked_dead = True
        with self.assertRaises(AssertionError):
            g._mark_dead(a)

    def test_mark_dead(self):
        def fresh_game():
            g = Game(3)
            for i in range(2):
                for j in range(2):
                    g.board[i][j].color = Color.white
            g.status = GameStatus.endgame
            return g

        # test that we can mark the group
        g = fresh_game()
        a = Action(
            ActionType.mark_dead, Color.white, datetime.now().timestamp(), (0, 0)
        )
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "4 stones marked as dead. Awaiting response...")
        self.assertTrue(
            all(g.board[i][j].marked_dead for i in range(2) for j in range(2))
        )
        self.assertIs(g.status, GameStatus.request_pending)
        self.assertIsNotNone(g.pending_request)
        self.assertIs(g.pending_request.request_type, RequestType.mark_dead)
        self.assertIs(g.pending_request.initiator, Color.white)

        # test that two consecutive mark dead operations fail
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg[:32], "Cannot mark stones as dead while")

        # test that mark dead on an empty point fails
        g = fresh_game()
        a.coords = (2, 2)
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "There is no group at (2, 2) to mark dead")

    def test_request_draw_assertions(self):
        g = Game(1)
        a = Action(ActionType.request_draw, Color.black, datetime.now().timestamp())

        # wrong status
        g.status = GameStatus.endgame
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.play

        # wrong type. Game.take_action should route this (correctly) to the
        # mark dead method, so we have to explicitly call the "private" method
        # to test the behavior
        a.action_type = ActionType.mark_dead
        with self.assertRaises(AssertionError):
            g._request_draw(a)

    def test_request_draw(self):
        g = Game(1)
        a = Action(ActionType.request_draw, Color.black, datetime.now().timestamp())

        # test that we can request a draw
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "Black requested a draw. Awaiting response...")
        self.assertIs(g.status, GameStatus.request_pending)
        self.assertIsNotNone(g.pending_request)
        self.assertIs(g.pending_request.request_type, RequestType.draw)
        self.assertIs(g.pending_request.initiator, Color.black)

        # test that two requests without a response fail
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "Cannot request draw while a previous request is pending")

        # test that requesting a draw outside of one's turn fails
        g = Game(1)
        a.color = Color.white
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "It isn't white's turn")

    def test_request_tally_score_assertions(self):
        g = Game(1)
        a = Action(
            ActionType.request_tally_score, Color.white, datetime.now().timestamp()
        )

        # wrong status
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.endgame

        # wrong type. Game.take_action should route this (correctly) to the
        # mark dead method, so we have to explicitly call the "private" method
        # to test the behavior
        a.action_type = ActionType.mark_dead
        with self.assertRaises(AssertionError):
            g._request_tally_score(a)

    def test_request_tally_score(self):
        g = Game(1)
        g.status = GameStatus.endgame
        a = Action(
            ActionType.request_tally_score, Color.white, datetime.now().timestamp()
        )

        # test that we can request a score tally
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(
            msg, ("White requested that the score be tallied. Awaiting response...")
        )
        self.assertIs(g.status, GameStatus.request_pending)
        self.assertIsNotNone(g.pending_request)
        self.assertIs(g.pending_request.request_type, RequestType.tally_score)
        self.assertIs(g.pending_request.initiator, Color.white)

        # test that two requests without a response fail
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(
            msg, "Cannot request score tally while a previous request is pending"
        )

    def test_respond_assertions(self):
        g = Game(1)
        a = Action(ActionType.accept, Color.black, datetime.now().timestamp())

        # wrong status
        with self.assertRaises(AssertionError):
            g.take_action(a)
        g.status = GameStatus.request_pending

        # wrong type. Game.take_action should route this (correctly) to the
        # mark dead method, so we have to explicitly call the "private" method
        # to test the behavior
        a.action_type = ActionType.mark_dead
        with self.assertRaises(AssertionError):
            g._respond(a)
        a.action_type = ActionType.accept

        # trying to respond to self
        g.pending_request = Request(RequestType.draw, Color.black)
        with self.assertRaises(AssertionError):
            g._respond(a)

    def test_respond(self):
        g = Game(1)
        ts = datetime.now().timestamp()
        for a in [
            Action(ActionType.request_draw, Color.black, ts),
            Action(ActionType.reject, Color.white, ts),
        ]:
            success, _ = g.take_action(a)
        self.assertTrue(success)
        self.assertIsNone(g.pending_request)

    @staticmethod
    def goto_endgame(g: Game, ts: float):
        """Assuming that the g is in play status and it's black's turn,
        transition to endgame by passing twice"""

        for c in reversed(Color):
            g.take_action(Action(ActionType.pass_turn, c, ts))

    def test_respond_mark_dead(self):
        g = Game(3)
        g.board[0][1].color = Color.white
        g.board[1][1].color = Color.white
        ts = datetime.now().timestamp()
        request = Action(ActionType.mark_dead, Color.white, ts, (1, 1))

        # negative response
        respond = Action(ActionType.reject, Color.black, ts)
        GameTestCase.goto_endgame(g, ts)
        g.take_action(request)
        success, msg = g.take_action(respond)
        self.assertIs(g.status, GameStatus.play)
        self.assertTrue(success)
        self.assertEqual(
            msg,
            (
                "Black rejected white's request to mark 2 white stones as dead."
                " Returning to play to resolve"
            ),
        )

        # positive response
        respond.action_type = ActionType.accept
        GameTestCase.goto_endgame(g, ts)
        g.take_action(request)
        success, msg = g.take_action(respond)
        self.assertIs(g.status, GameStatus.endgame)
        self.assertTrue(success)
        self.assertEqual(
            msg,
            "Black accepted white's request to mark 2 white stones as dead",
        )
        self.assertEqual(g.prisoners[Color.white], 0)
        self.assertEqual(g.prisoners[Color.black], 2)
        self.assertIsNone(g.board[0][1].color)
        self.assertIsNone(g.board[1][1].color)

    def test_respond_draw(self):
        g = Game(1)
        ts = datetime.now().timestamp()
        request = Action(ActionType.request_draw, Color.black, ts)

        # negative response
        respond = Action(ActionType.reject, Color.white, ts)
        g.take_action(request)
        success, msg = g.take_action(respond)
        self.assertIs(g.status, GameStatus.play)
        self.assertTrue(success)
        self.assertEqual(msg, "White rejected black's draw request")

        # positive response
        respond.action_type = ActionType.accept
        g.take_action(request)
        success, msg = g.take_action(respond)
        self.assertIs(g.status, GameStatus.complete)
        self.assertIs(g.result.result_type, ResultType.draw)
        self.assertIsNone(g.result.winner)
        self.assertTrue(success)
        self.assertEqual(msg, "White accepted black's draw request")

    def test_respond_tally_score(self):
        ts = datetime.now().timestamp()

        def ready_to_tally(komi: Optional[float] = None):
            """Return a ready to tally game"""
            g = Game(5, komi) if komi is not None else Game(5)
            for j in range(5):
                g.board[1][j].color = Color.white
                g.board[3][j].color = Color.black
            GameTestCase.goto_endgame(g, ts)
            return g

        g = ready_to_tally(0.0)
        request = Action(ActionType.request_tally_score, Color.white, ts)

        # negative response
        respond = Action(ActionType.reject, Color.black, ts)
        g.take_action(request)
        success, msg = g.take_action(respond)
        self.assertIs(g.status, GameStatus.endgame)
        self.assertTrue(success)
        self.assertEqual(msg, "Black rejected white's request to tally the score")

        # positive response (draw)
        respond.action_type = ActionType.accept
        g.take_action(request)
        success, msg = g.take_action(respond)
        self.assertIs(g.status, GameStatus.complete)
        self.assertTrue(success)
        self.assertEqual(msg, "Black accepted white's request to tally the score")
        self.assertEqual(g.territory[Color.white], 5)
        self.assertEqual(g.territory[Color.black], 5)
        self.assertIsNotNone(g.result)
        self.assertIs(g.result.result_type, ResultType.draw)
        self.assertIsNone(g.result.winner)

        # positive respond with winner
        g = ready_to_tally()
        g.take_action(request)
        g.take_action(respond)
        self.assertIsNotNone(g.result)
        self.assertIs(g.result.result_type, ResultType.standard_win)
        self.assertIsNotNone(g.result.winner)
        self.assertIs(g.result.winner, Color.white)

    def test_jsonifyable(self):
        g = Game(2)
        ts = datetime.now().timestamp()
        g.take_action(Action(ActionType.place_stone, Color.black, ts, (0, 0)))
        g.take_action(Action(ActionType.place_stone, Color.white, ts, (0, 1)))
        self.assertEqual(
            g.jsonifyable(),
            {
                "board": {
                    "size": 2,
                    "points": [
                        [["b", False, False, ""], ["w", False, False, ""]],
                        [["", False, False, ""], ["", False, False, ""]],
                    ],
                },
                "status": "play",
                "komi": 6.5,
                "prisoners": {"white": 0, "black": 0},
                "turn": "black",
                "territory": {"white": 0, "black": 0},
                "pendingRequest": None,
                "result": None,
                "lastMove": (0, 1),
            },
        )

        GameTestCase.goto_endgame(g, ts)
        g.take_action(Action(ActionType.request_tally_score, Color.white, ts))
        self.assertEqual(
            g.jsonifyable(),
            {
                "board": {
                    "size": 2,
                    "points": [
                        [["b", False, False, ""], ["w", False, False, ""]],
                        [["", False, False, ""], ["", False, False, ""]],
                    ],
                },
                "status": "request_pending",
                "komi": 6.5,
                "prisoners": {"white": 0, "black": 0},
                "turn": "black",
                "territory": {"white": 0, "black": 0},
                "pendingRequest": {"requestType": "tally_score", "initiator": "white"},
                "result": None,
                "lastMove": None,
            },
        )
        g.take_action(Action(ActionType.accept, Color.black, ts))
        self.assertEqual(
            g.jsonifyable(),
            {
                "board": {
                    "size": 2,
                    "points": [
                        [["b", False, False, ""], ["w", False, False, ""]],
                        [["", False, True, ""], ["", False, True, ""]],
                    ],
                },
                "status": "complete",
                "komi": 6.5,
                "prisoners": {"white": 0, "black": 0},
                "turn": "black",
                "territory": {"white": 0, "black": 0},
                "pendingRequest": None,
                "result": {"resultType": "standard_win", "winner": "white"},
                "lastMove": None,
            },
        )

    def test_deserialize(self):
        g = Game()
        # note that this only works because no actions have been taken. it would
        # otherwise fail for the reasons mentioned in the Game.deserialize
        # docstring
        self.assertEqual(Game.deserialize(g.jsonifyable()), g)

    def test_legal_moves(self):
        g = Game(3)
        g.board[0][1].color = Color.white
        g.board[1][0].color = Color.white
        self.assertSetEqual(
            {(2, 0), (1, 1), (0, 2), (2, 1), (1, 2), (2, 2)},
            set(g.legal_moves(Color.black)),
        )
        g.board[2][0].color = Color.black
        g.board[1][1].color = Color.black
        g.board[0][2].color = Color.black
        self.assertSetEqual(
            {(0, 0), (2, 1), (1, 2), (2, 2)},
            set(g.legal_moves(Color.black)),
        )
        g = Game(3)
        g.board[0][1].color = Color.white
        g.board[1][0].color = Color.white
        g.board[1][2].color = Color.white
        g.board[2][1].color = Color.white
        self.assertEqual(len(g.legal_moves(Color.black)), 0)

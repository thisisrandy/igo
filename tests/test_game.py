from datetime import datetime
from game import (
    Action,
    ActionType,
    Board,
    Color,
    Game,
    GameStatus,
    Point,
    RequestType,
    ResultType,
)
import unittest


class PointTestCase(unittest.TestCase):
    def test_json(self):
        self.assertEqual("___", Point().jsonifyable())
        self.assertEqual("w___", Point(Color.white).jsonifyable())
        self.assertEqual("b___", Point(Color.black).jsonifyable())
        self.assertEqual("w_d__", Point(Color.white, True).jsonifyable())
        self.assertEqual("b_d__", Point(Color.black, True).jsonifyable())
        self.assertEqual("b__c_", Point(Color.black, counted=True).jsonifyable())
        self.assertEqual(
            "__c_b", Point(counted=True, counts_for=Color.black).jsonifyable()
        )


class BoardTestCase(unittest.TestCase):
    def test_json(self):
        board = Board(3)
        self.assertEqual(
            board.jsonifyable(), [["", "", ""], ["", "", ""], ["", "", ""]]
        )
        board[0][1].color = Color.black
        self.assertEqual(
            board.jsonifyable(), [["", "b", ""], ["", "", ""], ["", "", ""]]
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


class GameTestCase(unittest.TestCase):
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
                ActionType.place_stone, Color.white, datetime.now().timestamp(), (0, 0)
            )
        )
        self.assertTrue(success)
        b[0][0].color = Color.white
        self.assertEqual(g.board, b)

    def test_turn(self):
        g = Game(3)
        success, msg = g.take_action(
            Action(
                ActionType.place_stone, Color.black, datetime.now().timestamp(), (0, 0)
            )
        )
        self.assertFalse(success)
        self.assertEqual(msg, "It isn't black's turn")
        g.take_action(
            Action(
                ActionType.place_stone, Color.white, datetime.now().timestamp(), (0, 0)
            )
        )
        success, msg = g.take_action(
            Action(
                ActionType.place_stone, Color.white, datetime.now().timestamp(), (0, 1)
            )
        )
        self.assertFalse(success)
        self.assertEqual(msg, "It isn't white's turn")

    def test_occupied(self):
        g = Game(3)
        g.take_action(
            Action(
                ActionType.place_stone, Color.white, datetime.now().timestamp(), (0, 0)
            )
        )
        success, msg = g.take_action(
            Action(
                ActionType.place_stone,
                Color.black,
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
            Action(ActionType.place_stone, Color.white, ts, (1, 0)),
            Action(ActionType.place_stone, Color.black, ts, (0, 0)),
            Action(ActionType.place_stone, Color.white, ts, (1, 1)),
            Action(ActionType.place_stone, Color.black, ts, (0, 1)),
            Action(ActionType.place_stone, Color.white, ts, (1, 2)),
            Action(ActionType.place_stone, Color.black, ts, (0, 2)),
        ]
        for a in actions:
            success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "Playing at (0, 2) is suicide")

    def test_ko(self):
        g = Game(4)
        ts = datetime.now().timestamp()
        actions = [
            Action(ActionType.place_stone, Color.white, ts, (1, 0)),
            Action(ActionType.place_stone, Color.black, ts, (2, 0)),
            Action(ActionType.place_stone, Color.white, ts, (0, 1)),
            Action(ActionType.place_stone, Color.black, ts, (3, 1)),
            Action(ActionType.place_stone, Color.white, ts, (1, 2)),
            Action(ActionType.place_stone, Color.black, ts, (2, 2)),
            Action(ActionType.place_stone, Color.white, ts, (2, 1)),
            Action(ActionType.place_stone, Color.black, ts, (1, 1)),
            Action(ActionType.place_stone, Color.white, ts, (2, 1)),
        ]
        for a in actions:
            success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "Playing at (2, 1) violates the simple ko rule")

    def test_capture(self):
        g = Game(5)
        ts = datetime.now().timestamp()
        actions = [
            Action(ActionType.place_stone, Color.white, ts, (0, 0)),
            Action(ActionType.place_stone, Color.black, ts, (1, 0)),
            Action(ActionType.place_stone, Color.white, ts, (0, 1)),
            Action(ActionType.place_stone, Color.black, ts, (1, 1)),
            Action(ActionType.place_stone, Color.white, ts, (0, 2)),
            Action(ActionType.place_stone, Color.black, ts, (2, 2)),
            Action(ActionType.place_stone, Color.white, ts, (1, 2)),
            Action(ActionType.place_stone, Color.black, ts, (1, 3)),
            Action(ActionType.place_stone, Color.white, ts, (0, 3)),
            Action(ActionType.place_stone, Color.black, ts, (0, 4)),
        ]
        for a in actions:
            success, msg = g.take_action(a)
        self.assertEqual(len(g.action_stack), len(actions))
        self.assertEqual(g.prisoners[Color.white], 0)
        self.assertEqual(g.prisoners[Color.black], 5)

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
        success, msg = g.take_action(Action(ActionType.pass_turn, Color.white, ts))
        self.assertTrue(success)
        self.assertEqual(msg, "White passed on their turn")
        self.assertTrue(g.turn is Color.black)
        self.assertTrue(g.status is GameStatus.play)
        success, msg = g.take_action(Action(ActionType.pass_turn, Color.black, ts))
        self.assertTrue(success)
        self.assertEqual(msg, "Black passed on their turn")
        self.assertTrue(g.turn is Color.white)
        self.assertTrue(g.status is GameStatus.endgame)

    def test_resign_assertions(self):
        g = Game(1)
        a = Action(ActionType.resign, Color.white, datetime.now().timestamp())

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
        a = Action(ActionType.resign, Color.white, datetime.now().timestamp())
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "White resigned")
        self.assertEqual(g.status, GameStatus.complete)
        self.assertIsNotNone(g.result)
        self.assertEqual(g.result.result_type, ResultType.resignation)
        self.assertEqual(g.result.winner, Color.black)

        # test that black can resign on white's turn
        g = Game(1)
        a.color = Color.black
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "Black resigned")

    def test_mark_dead_assertions(self):
        g = Game(1)

        # no coords
        a = Action(ActionType.mark_dead, Color.white, datetime.now().timestamp())
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
        a = Action(ActionType.request_draw, Color.white, datetime.now().timestamp())

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
        a = Action(ActionType.request_draw, Color.white, datetime.now().timestamp())

        # test that we can request a draw
        success, msg = g.take_action(a)
        self.assertTrue(success)
        self.assertEqual(msg, "White requested a draw. Awaiting response...")
        self.assertIs(g.status, GameStatus.request_pending)
        self.assertIsNotNone(g.pending_request)
        self.assertIs(g.pending_request.request_type, RequestType.draw)
        self.assertIs(g.pending_request.initiator, Color.white)

        # test that two requests without a response fail
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "Cannot request draw while a previous request is pending")

        # test that requesting a draw outside of one's turn fails
        g = Game(1)
        a.color = Color.black
        success, msg = g.take_action(a)
        self.assertFalse(success)
        self.assertEqual(msg, "It isn't black's turn")

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

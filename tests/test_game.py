from datetime import datetime
from game import Action, ActionType, Board, Color, Game, GameStatus, Point
import unittest


class PointTestCase(unittest.TestCase):
    def test_json(self):
        self.assertEqual("", Point().jsonifyable())
        self.assertEqual("w", Point(Color.white).jsonifyable())
        self.assertEqual("b", Point(Color.black).jsonifyable())
        self.assertEqual("wd", Point(Color.white, True).jsonifyable())
        self.assertEqual("bd", Point(Color.black, True).jsonifyable())


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

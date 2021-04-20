from game import Board, Color, Point
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
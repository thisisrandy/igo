from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
from uuid import uuid4


class Color(Enum):
    white = auto()
    black = auto()


class ActionType(Enum):
    placement = auto()
    pass_move = auto()
    mark_dead = auto()
    draw_game = auto()
    end_game = auto()
    accept = auto()
    reject = auto()


class GameStatus(Enum):
    play = auto()
    endgame = auto()
    complete = auto()


@dataclass
class Action:
    """
    Container class for moves

    Attributes:

        action_type: ActionType - the type of this action

        color: Color - which player took the action

        coords: Optional[Tuple[int, int]] - if relevant given action_type,
        the coordinates of the point on which the action was taken

        timestamp: float - server time at which this action was created
    """

    action_type: ActionType
    color: Color
    coords: Optional[Tuple[int, int]]
    timestamp: float


@dataclass
class Point:
    """
    Container class for board points

    Attributes:

        color: Optional[Color] - the color of the stone at this point or None if empty

        marked_dead: bool - indicator of whether this stone has been marked
        dead. meaningless if color is None
    """

    color: Optional[Color] = None
    marked_dead: bool = False

    def __repr__(self) -> str:
        return ("" if not self.color else "w" if self.color == Color.white else "b") + (
            "d" if self.marked_dead else ""
        )


class Board:
    """
    Subscriptable 2d container class for the full board. `Board()[i][j] -> Point`

    Attributes:

        size: int - the number of points on either side of the board
    """

    class _BoardRow:
        def __init__(self, size: int) -> None:
            self.row = [Point() for _ in range(size)]

        def __getitem__(self, key: int) -> Point:
            return self.row[key]

        def __repr__(self) -> str:
            return str(self.row)

    def __init__(self, size: int = 19) -> None:
        self.size = size
        self._rows = [Board._BoardRow(size) for _ in range(size)]

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, key: int) -> Board._BoardRow:
        return self._rows[key]

    def __repr__(self) -> str:
        return str(self._rows)


class Game:
    """
    The state and rule logic of a go game

    Attributes:

        keys: Dict[Color] - truncated (10 char) UUIDs for black and white players.
        the creating player is informed of both keys upon game creation,
        and all subsequent actions from either player require their key

        status: GameStatus - indicator of the status of the game

        action_stack: List[Action] - the complete list of valid actions taken
        throughout the game. also an indicator of whose turn it is during
        play (white if the stack is empty, otherwise the color not at the top
        of the stack)

        board: Board - the game board

    """

    def __init__(self, size: int = 19) -> None:
        self.keys: Dict[Color] = {
            Color.white: uuid4().hex[-10:],
            Color.black: uuid4().hex[-10:],
        }
        self.status: GameStatus = GameStatus.play
        self.action_stack: List[Action] = []
        self.board: Board = Board(size)

    def __repr__(self) -> str:
        return f"Game(keys={self.keys}, status={self.status}, action_stack={self.action_stack}, board={self.board})"

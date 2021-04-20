from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4
from copy import deepcopy


class Color(Enum):
    white = auto()
    black = auto()

    def inverse(self) -> Color:
        """Return white if black and black if white"""

        return Color.black if self is Color.white else Color.white


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
        return repr(str(self))

    def __str__(self) -> str:
        return ("" if not self.color else "w" if self.color is Color.white else "b") + (
            "d" if self.marked_dead else ""
        )

    def __eq__(self, o: object) -> bool:
        """Color equality only, as this is only for the purpose of detecting ko"""

        if not isinstance(o, Point):
            return False
        return self.color is o.color

    def jsonifyable(self) -> str:
        """Return a representation which can be readily JSONified"""

        return str(self)


class Board:
    """
    Subscriptable 2d container class for the full board. `Board()[i][j] -> Point`

    Attributes:

        size: int - the number of points on either side of the board
    """

    class _BoardRow:
        def __init__(self, size: int) -> None:
            self._row = [Point() for _ in range(size)]

        def __getitem__(self, key: int) -> Point:
            return self._row[key]

        def __repr__(self) -> str:
            return str(self._row)

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Board._BoardRow):
                return False
            return self._row == other._row

        def jsonifyable(self) -> List[str]:
            """Return a representation which can be readily JSONified"""

            return [p.jsonifyable() for p in self._row]

    def __init__(self, size: int = 19) -> None:
        self.size = size
        self._rows = [Board._BoardRow(size) for _ in range(size)]

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, key: int) -> Board._BoardRow:
        return self._rows[key]

    def __repr__(self) -> str:
        return str(self._rows)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return False
        return self.size == other.size and all(
            r == o for r, o in zip(self._rows, other._rows)
        )

    def jsonifyable(self) -> List[List[str]]:
        """Return a representation which can be readily JSONified"""

        return [r.jsonifyable() for r in self._rows]


class Game:
    """
    The state and rule logic of a go game

    Attributes:

        keys: Dict[Color, str] - truncated (10 char) UUIDs for black and
        white players. the creating player is informed of both keys upon game
        creation, and all subsequent actions from either player require their
        key

        status: GameStatus - indicator of the status of the game

        turn: Color - during play, indicator of whose turn it is (meaningless
        otherwise)

        action_stack: List[Action] - the complete list of valid actions taken
        throughout the game

        board: Board - the game board

        prisoners: Dict[Color, int] - the number of prisoners taken by each player

    """

    def __init__(self, size: int = 19, komi: float = 6.5) -> None:
        self.keys: Dict[Color, str] = {
            Color.white: uuid4().hex[-10:],
            Color.black: uuid4().hex[-10:],
        }
        self.status: GameStatus = GameStatus.play
        self.turn: Color = Color.white
        self.action_stack: List[Action] = []
        self.board: Board = Board(size)
        self.komi: float = komi
        self.prisoners: Dict[Color, int] = {Color.white: 0, Color.black: 0}
        self._prev_board: Board = None

    def __repr__(self) -> str:
        return (
            f"Game(keys={self.keys}"
            f", status={self.status}"
            f", turn={self.turn}"
            f", action_stack={self.action_stack}"
            f", board={self.board}"
            f", komi={self.komi}"
            f", prisoners={self.prisoners}"
            f", _prev_board={self._prev_board})"
        )

    def take_action(self, action: Action) -> Tuple[bool, str]:
        """Attempt to take an action. Return True if that action was valid
        and False otherwise"""

        # TODO: remove this once all action types are handled
        success, msg = False, ""

        if action.action_type == ActionType.placement:
            success, msg = self._place_stone(action)
        elif action.action_type == ActionType.pass_move:
            pass
        elif action.action_type == ActionType.mark_dead:
            pass
        elif action.action_type == ActionType.draw_game:
            pass
        elif action.action_type == ActionType.end_game:
            pass
        elif action.action_type == ActionType.accept:
            pass
        elif action.action_type == ActionType.reject:
            pass

        if success:
            self.action_stack.append(action)
        return success, msg

    def _place_stone(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type == ActionType.placement
        assert self.status == GameStatus.play

        if action.color is not self.turn:
            return (False, f"It isn't {action.color.name}'s turn")

        i, j = action.coords
        if self.board[i][j].color:
            return (False, f"Point {action.coords} is occupied")

        # we will proceed by copying the board and then placing this stone.
        # first, we remove any captured stones. if we don't remove anything in
        # this way, we check if the group that the placed stone is part of is
        # not surrounded (no suicide rule). finally, we check that the board
        # has not returned to the last previous board position (simple ko). if
        # the move is in fact legal, we cycle in the new board position, update
        # prisoner counts if any stones were captured, and cycle the turn
        # attribute

        new_board: Board = deepcopy(self.board)
        new_board[i][j].color = action.color
        opponent = action.color.inverse()
        captured = 0

        for ii, jj in self._adjacencies(i, j):
            if new_board[ii][jj].color is opponent:
                (group, alive) = self._gather(new_board, ii, jj)
                if not alive:
                    for iii, jjj in group:
                        new_board[iii][jjj].color = None
                    captured += len(group)

        if not captured and not self._gather(new_board, i, j)[1]:
            return (False, f"Playing at {action.coords} is suicide")

        if new_board == self._prev_board:
            return (False, f"Playing at {action.coords} violates the simple ko rule")

        self._prev_board, self.board = self.board, new_board
        self.prisoners[action.color] += captured
        self.turn = self.turn.inverse()

        return (
            True,
            f"Successfully placed a {action.color.name} stone at {action.coords}",
        )

    def _adjacencies(self, i: int, j: int) -> Set[Tuple[int, int]]:
        """Utility to return the set of in bounds points adjacent to (i, j)
        given self.board"""

        return {
            (ii, jj)
            for ii, jj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))
            if 0 <= ii < self.board.size and 0 <= jj < self.board.size
        }

    def _gather(
        self, board: Board, i: int, j: int
    ) -> Tuple[Set[Tuple[int, int]], bool]:
        """Gather all of the stones in the same group as board[i][j] and
        return their coordinates in a set along with an indicator of whether
        or not they are alive"""

        assert board[i][j].color

        color = board[i][j].color
        group = {(i, j)}
        stack = [(i, j)]
        alive = False

        while stack:
            adjacencies = self._adjacencies(*stack.pop()) - group
            alive = alive or any(board[ii][jj].color is None for ii, jj in adjacencies)
            to_add = [
                (ii, jj) for ii, jj in adjacencies if board[ii][jj].color is color
            ]
            group.update(to_add)
            stack.extend(to_add)

        return (group, alive)

    def ahead_of(self, timestamp: float) -> bool:
        """If the last successful action was after timestamp, return True
        and False if this is a new game or otherwise"""

        return self.action_stack and self.action_stack[-1].timestamp > timestamp

    def jsonifyable(self) -> Dict:
        """Return a representation which can be readily JSONified. In
        particular, return a dictionary with the board, game status, komi,
        prisoner counts, and whose turn it is, noting that the last datum is
        meaningless if the game is over"""

        return {
            "board": self.board.jsonifyable(),
            "status": self.status.name,
            "komi": self.komi,
            "prisoners": {
                Color.white.name: self.prisoners[Color.white],
                Color.black.name: self.prisoners[Color.black],
            },
            "turn": self.turn.name,
        }
from __future__ import annotations
from dataclassy import dataclass
from enum import Enum, auto
from igo.serialization import JsonifyableBase, JsonifyableBaseDataClass
from typing import Dict, List, Optional, Set, Tuple
from copy import deepcopy


class Color(Enum):
    white = auto()
    black = auto()

    def inverse(self) -> Color:
        """Return white if black and black if white"""

        return Color.black if self is Color.white else Color.white

    def to_short(self) -> str:
        """Return the first letter of the color name for compact serialization"""

        return self.name[0]

    @staticmethod
    def from_short(short_name: str) -> Optional[Color]:
        """Inverse of `to_short` which returns None when `short_name` is the
        empty string"""

        if not short_name:
            return None
        for c in Color:
            if c.to_short() == short_name:
                return c
        raise ValueError(f"'{short_name}' is not a valid short Color name")


class ActionType(Enum):
    place_stone = auto()
    pass_turn = auto()
    mark_dead = auto()
    request_draw = auto()
    resign = auto()
    request_tally_score = auto()
    accept = auto()
    reject = auto()


class GameStatus(Enum):
    play = auto()
    endgame = auto()
    complete = auto()
    request_pending = auto()


class RequestType(Enum):
    mark_dead = auto()
    draw = auto()
    tally_score = auto()


class ResultType(Enum):
    standard_win = auto()
    draw = auto()
    resignation = auto()


@dataclass(slots=True)
class Action:
    """
    Container class for moves

    Attributes:

        action_type: ActionType - the type of this action

        color: Color - which player took the action

        timestamp: float - server time at which this action was created

        coords: Optional[Tuple[int, int]] - if relevant given action_type,
        the coordinates of the point on which the action was taken
    """

    action_type: ActionType
    color: Color
    timestamp: float
    coords: Optional[Tuple[int, int]] = None


class Request(JsonifyableBaseDataClass):
    """
    Container class for requests that are pending response

    Attributes:

        request_type: RequestType - the type of this request

        initiator: Color - the initiating player, i.e. initiator is waiting
        for initiator.inverse() to respond
    """

    request_type: RequestType
    initiator: Color

    def jsonifyable(self):
        """Return a representation which can be readily JSONified"""

        return {"requestType": self.request_type.name, "initiator": self.initiator.name}

    @classmethod
    def _deserialize(cls, data: Dict) -> Request:
        return Request(RequestType[data["requestType"]], Color[data["initiator"]])


class Result(JsonifyableBaseDataClass):
    """
    Container class for the final result of the game

    Attributes:

        result_type: ResultType - the way in which the game ended

        winner: Optional[Color] - the player who won, if anyone
    """

    result_type: ResultType
    winner: Optional[Color] = None

    def jsonifyable(self):
        """Return a representation which can be readily JSONified"""

        return {
            "resultType": self.result_type.name,
            "winner": self.winner.name if self.winner else None,
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> Result:
        return Result(
            ResultType[data["resultType"]],
            Color[data["winner"]] if data["winner"] else None,
        )


class Point(JsonifyableBaseDataClass):
    """
    Container class for board points

    Attributes:

        color: Optional[Color] - the color of the stone at this point or None if empty

        marked_dead: bool - indicator of whether this stone has been marked
        dead. meaningless if color is None

        counted: bool - indicator of whether this point has been counted
        during the scoring phase. under Japanese rules, this is only
        applicable to empty points

        counts_for: Optional[Color] - if this point has been counted as part
        of a player's territory, this attribute indicates which one
    """

    color: Optional[Color] = None
    marked_dead: bool = False
    counted: bool = False
    counts_for: Optional[Color] = None

    def __str__(self) -> str:
        return str(self.jsonifyable())

    def __eq__(self, o: object) -> bool:
        """Color equality only, as this is only for the purpose of detecting ko"""

        if not isinstance(o, Point):
            return False
        return self.color is o.color

    def jsonifyable(self) -> str:
        """Return a representation which can be readily JSONified"""

        return [
            ("" if not self.color else self.color.to_short()),
            self.marked_dead,
            self.counted,
            ("" if not self.counts_for else self.counts_for.to_short()),
        ]

    @classmethod
    def _deserialize(cls, data: List) -> Point:
        return Point(
            Color.from_short(data[0]),
            *data[1:3],
            Color.from_short(data[3]),
        )

    def __deepcopy__(self, memo: Dict) -> Point:
        return Point(self.color, self.marked_dead, self.counted, self.counts_for)


class Board(JsonifyableBase):
    """
    Subscriptable 2d container class for the full board. `Board()[i][j] -> Point`

    Attributes:

        size: int - the number of points on either side of the board
    """

    class _BoardRow(JsonifyableBase):

        __slots__ = "_row"

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

        def __deepcopy__(self, memo: Dict) -> Board._BoardRow:
            dup: Board._BoardRow = self.__new__(self.__class__)
            dup._row = [deepcopy(p, memo) for p in self._row]
            return dup

        @classmethod
        def _deserialize(cls, data: List) -> Board._BoardRow:
            self: Board._BoardRow = cls.__new__(cls)
            self._row = [Point.deserialize(p) for p in data]
            return self

    __slots__ = ("size", "_rows")

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

        return {"size": self.size, "points": [r.jsonifyable() for r in self._rows]}

    def __deepcopy__(self, memo: Dict) -> Board:
        """
        NOTE: a naive deepcopy of board was the single most expensive operation
        the game server was undertaking in profiling runs. implementing
        __deepcopy__ for Board and its attributes shaves this down by about a
        factor of 10
        """

        dup: Board = self.__new__(self.__class__)
        dup.size = self.size
        dup._rows = [deepcopy(r, memo) for r in self._rows]
        return dup

    @classmethod
    def _deserialize(cls, data: Dict) -> Board:
        self: Board = cls.__new__(cls)
        self.size = data["size"]
        self._rows = [Board._BoardRow.deserialize(row) for row in data["points"]]
        return self


class Game(JsonifyableBase):
    """
    The state and rule logic of a go game

    Attributes:

        status: GameStatus - indicator of the status of the game

        turn: Color - during play, indicator of whose turn it is (meaningless
        otherwise)

        action_stack: List[Action] - the complete list of valid actions taken
        throughout the game

        board: Board - the game board

        prisoners: Dict[Color, int] - the number of prisoners taken by each player

        territory: Dict[Color, int] - the number of empty points enclosed by
        each player's stones, calculated at the end of the game and zero
        otherwise

        pending_request: Optional[Request] - if there is a pending request in
        need of response, it is stored here

        result: Optional[Result] - the result of the game, set only once it
        has been resolved
    """

    # TODO: Add export to SGF (Smart Game Format). We ought to be able to export
    # at this level, enrich with player info and send at the server level, and
    # request export from the UI

    __slots__ = (
        "status",
        "turn",
        "action_stack",
        "board",
        "komi",
        "prisoners",
        "territory",
        "pending_request",
        "result",
        "_prev_board",
    )

    def __init__(self, size: int = 19, komi: float = 6.5) -> None:
        self.status: GameStatus = GameStatus.play
        self.turn: Color = Color.black
        self.action_stack: List[Action] = []
        self.board: Board = Board(size)
        self.komi: float = komi
        self.prisoners: Dict[Color, int] = {Color.white: 0, Color.black: 0}
        self.territory: Dict[Color, int] = {Color.white: 0, Color.black: 0}
        self.pending_request: Optional[Request] = None
        self.result: Optional[Result] = None
        self._prev_board: Board = None

    def __repr__(self) -> str:
        return (
            f"Game(status={self.status}"
            f", turn={self.turn}"
            f", action_stack={self.action_stack}"
            f", board={self.board}"
            f", komi={self.komi}"
            f", prisoners={self.prisoners}"
            f", territory={self.territory}"
            f", pending_request={self.pending_request}"
            f", result={self.result}"
            f", _prev_board={self._prev_board})"
        )

    def __eq__(self, o: object) -> bool:
        """Equality is judged by comparing initializers and the action stack,
        which together fully determine the state of the game, provided of
        course that only the public interface has been accessed (this
        function's return is undefined otherwise). NB: this is a state
        comparison, *not* a unique game comparison. Game does not contain any
        data which uniquely identify it beyond its state (though timestamp,
        which is *not* used here, comes close), which is by design"""

        if not isinstance(o, Game):
            return False
        return (
            self.board.size == o.board.size
            and self.komi == o.komi
            and self.action_stack == o.action_stack
        )

    def take_action(self, action: Action) -> Tuple[bool, str]:
        """Attempt to take an action. Return a tuple of True if that action
        was valid and False otherwise, and an explanatory message in either
        case"""

        if self.action_stack:
            assert self.action_stack[-1].timestamp <= action.timestamp

        if action.action_type is ActionType.place_stone:
            success, msg = self._place_stone(action)
        elif action.action_type is ActionType.pass_turn:
            success, msg = self._pass_turn(action)
        elif action.action_type is ActionType.resign:
            success, msg = self._resign(action)
        elif action.action_type is ActionType.mark_dead:
            success, msg = self._mark_dead(action)
        elif action.action_type is ActionType.request_draw:
            success, msg = self._request_draw(action)
        elif action.action_type is ActionType.request_tally_score:
            success, msg = self._request_tally_score(action)
        elif action.action_type is ActionType.accept:
            success, msg = self._respond(action)
        elif action.action_type is ActionType.reject:
            success, msg = self._respond(action)
        else:
            raise RuntimeError(f"Unknown ActionType encountered: {action.action_type}")

        if success:
            self.action_stack.append(action)
        return success, msg

    def _place_stone(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type is ActionType.place_stone
        assert self.status is GameStatus.play
        assert action.coords

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
                (group, alive) = self._gather(ii, jj, new_board)
                if not alive:
                    for iii, jjj in group:
                        new_board[iii][jjj].color = None
                    captured += len(group)

        if not captured and not self._gather(i, j, new_board)[1]:
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

    def _pass_turn(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type is ActionType.pass_turn
        assert self.status is GameStatus.play

        if action.color is not self.turn:
            return (False, f"It isn't {action.color.name}'s turn")

        # if both players pass in succession, the endgame commences. otherwise,
        # pass simply flips the turn and goes on the stack

        if (
            self.action_stack
            and self.action_stack[-1].action_type is ActionType.pass_turn
        ):
            self.status = GameStatus.endgame

        self.turn = self.turn.inverse()

        return True, f"{action.color.name.capitalize()} passed on their turn"

    def _resign(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type is ActionType.resign
        assert self.status is GameStatus.play

        self.status = GameStatus.complete
        self.result = Result(ResultType.resignation, action.color.inverse())

        return True, f"{action.color.name.capitalize()} resigned"

    def _mark_dead(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type is ActionType.mark_dead
        assert self.status in (GameStatus.endgame, GameStatus.request_pending)
        assert action.coords

        if self.status is GameStatus.request_pending:
            return (
                False,
                "Cannot mark stones as dead while a previous request is pending",
            )

        i, j = action.coords
        if not self.board[i][j].color:
            return False, (f"There is no group at {action.coords} to mark dead")

        group, _ = self._gather(i, j)
        for ii, jj in group:
            assert not self.board[ii][jj].marked_dead
            self.board[ii][jj].marked_dead = True

        self.status = GameStatus.request_pending
        self.pending_request = Request(RequestType.mark_dead, action.color)

        return True, f"{len(group)} stones marked as dead. Awaiting response..."

    def _respond_mark_dead(self, action: Action) -> str:
        """This function should only ever be called from _respond, which
        makes the appropriate assertions for all types of requests. Any other
        usage is undefined"""

        def count_and_clear(just_count: bool = False) -> Tuple[int, Color]:
            """As only one group at a time can be marked dead, we can simply
            scan the board for points marked dead, counting and unmarking
            them as we go. If just_count is False, we will additionally clear
            the pieces by setting that Point's color to None"""

            num_marked = 0
            color = None

            for i in range(self.board.size):
                for j in range(self.board.size):
                    if self.board[i][j].marked_dead:
                        if color is None:
                            color = self.board[i][j].color
                        elif color is not self.board[i][j].color:
                            raise RuntimeError(
                                "More than one color of stones at a time is currently"
                                " marked dead, which should never happen"
                            )
                        self.board[i][j].marked_dead = False
                        if not just_count:
                            self.board[i][j].color = None
                        num_marked += 1

            if not num_marked:
                raise RuntimeError(
                    "No stones are marked as dead, but we are handling a response to"
                    " them having been marked"
                )

            return num_marked, color

        if action.action_type is ActionType.accept:
            num_marked, color = count_and_clear()
            self.prisoners[color.inverse()] += num_marked
            self.status = GameStatus.endgame
        else:  # ActionType.reject
            num_marked, color = count_and_clear(True)
            self.status = GameStatus.play

        return f"request to mark {num_marked} {color.name} stones as dead" + (
            ". Returning to play to resolve"
            if action.action_type is ActionType.reject
            else ""
        )

    def _request_draw(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type is ActionType.request_draw
        assert self.status in (GameStatus.play, GameStatus.request_pending)

        if action.color is not self.turn:
            return (False, f"It isn't {action.color.name}'s turn")

        if self.status is GameStatus.request_pending:
            return False, "Cannot request draw while a previous request is pending"

        self.status = GameStatus.request_pending
        self.pending_request = Request(RequestType.draw, action.color)

        return (
            True,
            f"{action.color.name.capitalize()} requested a draw. Awaiting response...",
        )

    def _respond_draw(self, action: Action) -> str:
        """This function should only ever be called from _respond, which
        makes the appropriate assertions for all types of requests. Any other
        usage is undefined"""

        if action.action_type is ActionType.accept:
            self.status = GameStatus.complete
            self.result = Result(ResultType.draw)
        else:  # ActionType.reject
            self.status = GameStatus.play

        return "draw request"

    def _request_tally_score(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type is ActionType.request_tally_score
        assert self.status in (GameStatus.endgame, GameStatus.request_pending)

        if self.status is GameStatus.request_pending:
            return (
                False,
                "Cannot request score tally while a previous request is pending",
            )

        self.status = GameStatus.request_pending
        self.pending_request = Request(RequestType.tally_score, action.color)

        return (
            True,
            (
                f"{action.color.name.capitalize()} requested that the score be tallied."
                " Awaiting response..."
            ),
        )

    def _respond_draw_tally_score(self, action: Action) -> str:
        """This function should only ever be called from _respond, which
        makes the appropriate assertions for all types of requests. Any other
        usage is undefined"""

        if action.action_type is ActionType.accept:
            self._count_territory()
            white_score = (
                self.komi + self.prisoners[Color.white] + self.territory[Color.white]
            )
            black_score = self.prisoners[Color.black] + self.territory[Color.black]
            self.result = Result(
                (
                    ResultType.draw
                    if white_score == black_score
                    else ResultType.standard_win
                ),
                (
                    Color.white
                    if white_score > black_score
                    else Color.black
                    if black_score > white_score
                    else None
                ),
            )
            self.status = GameStatus.complete
        else:  # ActionType.reject
            self.status = GameStatus.endgame

        return "request to tally the score"

    def _count_territory(self) -> None:
        # We proceed by scanning the board for empty points, keeping track of
        # those already processed by marking them as counted. When we find an
        # uncounted empty point, we collect all empty points connected to it
        # along with the colors of the stones on the group's borders. If there
        # is only one color on the border, we assign the points to that color
        # and mark the points as such. Otherwise (zero or two border colors),
        # we mark the group as neutral and assign no points

        for i in range(self.board.size):
            for j in range(self.board.size):
                if self.board[i][j].color is None and not self.board[i][j].counted:
                    stack = [(i, j)]
                    colors = set()
                    group = set()
                    border = set()
                    while stack:
                        ii, jj = stack.pop()
                        if (ii, jj) in group | border:
                            continue
                        color = self.board[ii][jj].color
                        if color is None:
                            group.add((ii, jj))
                            stack.extend(self._adjacencies(ii, jj))
                        else:
                            border.add((ii, jj))
                            colors.add(color)
                    counts_for = colors.pop() if len(colors) == 1 else None
                    for ii, jj in group:
                        self.board[ii][jj].counted = True
                        self.board[ii][jj].counts_for = counts_for
                    if counts_for:
                        self.territory[counts_for] += len(group)

    def _respond(self, action: Action) -> Tuple[bool, str]:
        assert action.action_type in (ActionType.accept, ActionType.reject)
        assert self.status is GameStatus.request_pending
        assert self.pending_request is not None
        assert self.pending_request.initiator is not action.color

        if self.pending_request.request_type is RequestType.mark_dead:
            response_string = self._respond_mark_dead(action)
        elif self.pending_request.request_type is RequestType.draw:
            response_string = self._respond_draw(action)
        elif self.pending_request.request_type is RequestType.tally_score:
            response_string = self._respond_draw_tally_score(action)
        else:
            raise RuntimeError(
                f"Unknown RequestType encountered: {self.pending_request.request_type}"
            )

        self.pending_request = None
        return (
            True,
            (
                "%s %sed %s's %s"
                % (
                    action.color.name.capitalize(),
                    action.action_type.name,
                    action.color.inverse().name,
                    response_string,
                )
            ),
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
        self, i: int, j: int, board: Board = None
    ) -> Tuple[Set[Tuple[int, int]], bool]:
        """Gather all of the stones in the same group as board[i][j] and
        return their coordinates in a set along with an indicator of whether
        or not they are alive. Note that board is set to self.board if
        unspecified"""

        if not board:
            board = self.board

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

    def version(self) -> int:
        """Return the game version, equal to the length of the action stack"""

        return len(self.action_stack)

    def last_move(self) -> Optional[Tuple[int, int]]:
        """Return the coords of the last successful stone placement, if
        applicable"""

        return (
            self.action_stack[-1].coords
            if self.action_stack
            and self.action_stack[-1].action_type is ActionType.place_stone
            else None
        )

    def jsonifyable(self) -> Dict:
        """Return a representation which can be readily JSONified. In
        particular, return a dictionary with the board, game status, komi,
        prisoner counts, whose turn it is, territory, any pending request, the
        game result, and the coordinates of the last stone placed, noting that
        some of these are meaningless or unavailable depending on the game
        state"""

        return {
            "board": self.board.jsonifyable(),
            "status": self.status.name,
            "komi": self.komi,
            "prisoners": {
                Color.white.name: self.prisoners[Color.white],
                Color.black.name: self.prisoners[Color.black],
            },
            "turn": self.turn.name,
            "territory": {
                Color.white.name: self.territory[Color.white],
                Color.black.name: self.territory[Color.black],
            },
            "pendingRequest": self.pending_request.jsonifyable()
            if self.pending_request
            else None,
            "result": self.result.jsonifyable() if self.result else None,
            "lastMove": self.last_move(),
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> Game:
        """Note that `Game.jsonifyable` strips out the action stack and previous
        board. As such, they are not available in the deserialized version
        produced by this method, with one exception: if `lastMove` is available,
        a single action will be pushed onto the stack with the last move
        coordinates and a fake timestamp"""

        self: Game = cls.__new__(cls)
        self.board = Board.deserialize(data["board"])
        self.status = GameStatus[data["status"]]
        self.komi = data["komi"]
        prisoners = data["prisoners"]
        self.prisoners = {Color[c]: prisoners[c] for c in prisoners}
        self.turn = Color[data["turn"]]
        territory = data["territory"]
        self.territory = {Color[c]: territory[c] for c in territory}
        pending_request = data["pendingRequest"]
        self.pending_request = (
            Request.deserialize(pending_request) if pending_request else None
        )
        result = data["result"]
        self.result = Result.deserialize(result) if result else None
        self.action_stack = []
        if data["lastMove"]:
            self.action_stack.append(
                Action(
                    ActionType.place_stone,
                    self.turn.inverse(),
                    0,
                    tuple(data["lastMove"]),
                )
            )
        self._prev_board = None
        return self

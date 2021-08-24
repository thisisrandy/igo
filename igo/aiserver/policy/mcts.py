from __future__ import annotations
from copy import deepcopy
from typing import Optional
from random import randrange
from dataclassy import dataclass
from igo.game import Action, ActionType, Color, Game
from igo.aiserver.policy.base import PlayPolicyBase
from math import sqrt, log


@dataclass(slots=True)
class TreeNode:
    game: Game
    player_color: Color
    parent: Optional[TreeNode] = None
    _wins: int = 0
    _num_simulations: int = 0
    _children: list[TreeNode] = []
    _moves: Optional[list[tuple[int, int]]] = None

    PASS = (-1, -1)
    EXPLORATION_COEFF = sqrt(2)

    def __post_init__(self) -> None:
        self._moves = self.game.legal_moves()
        self._moves.append(TreeNode.PASS)

    @property
    def simulated(self) -> bool:
        return self._num_simulations > 0

    @property
    def has_unsimulated_children(self) -> bool:
        return len(self._moves) > 0

    @property
    def has_children(self) -> bool:
        return len(self._children) > 0

    @property
    def choice_value(self) -> float:
        """
        Calculate the expression given at
        https://en.wikipedia.org/wiki/Monte_Carlo_tree_search#Exploration_and_exploitation
        """

        assert (
            self.simulated
        ), "Choice value cannot be computed for as yet unsimulated nodes"
        assert (
            self.parent is not None
        ), "Choice value cannot be computed on the root node"

        return self._wins / self._num_simulations + TreeNode.EXPLORATION_COEFF * sqrt(
            log(self.parent._num_simulations) / self._num_simulations
        )

    def select_move(self) -> tuple[int, int]:
        """
        Select and remove a random move from the as yet unsimulated moves set
        """

        assert (
            self.has_unsimulated_children
        ), "Cannot select move when all moves have already been simulated"

        # we don't care about the order of self._moves, so we can avoid a linear
        # list removal cost by selecting an element and then replacing it with
        # the final element, which we pop off the top
        idx = randrange(0, len(self._moves))
        res = self._moves[idx]
        top = self._moves.pop()
        # equiv idx < len(self._moves), i.e. we didn't select the last element
        if top is not res:
            self._moves[idx] = top
        return res

    @property
    def best_child(self) -> TreeNode:
        """
        Return the child with the highest `choice_value`
        """

        assert self.has_children, "No actions have been simulated past this point"

        return max(self._children, key=lambda c: c.choice_value)

    def run_simulation(self) -> bool:
        """
        Starting from a randomly chosen unsimulated child, play a game to
        completion and backpropagate the results. Return True if the simulated
        path resulted in a win and False otherwise (draw or loss)
        """

        # TODO: check game status, and if in endgame, take all actions to remove
        # dead groups and tally the score (right now, this just drills down
        # until there aren't any legal moves left and then blows up for that
        # reason). there's going to need to be some logic in Game to do this.
        # seki is too hard to detect in general, but we can do a basic eye check
        # on groups, which is probably good enough

        if not self.has_unsimulated_children:
            res = self.best_child.run_simulation()
        else:
            advanced_game: Game = deepcopy(self.game)
            advanced_game.take_action(
                Action(ActionType.place_stone, self.game.turn, 0.0, self.select_move())
            )
            child = TreeNode(advanced_game, self.player_color, self)
            self._children.append(child)
            res = child.run_simulation()

        self._num_simulations += 1
        self._wins += res
        return res


class MCTSPolicy(PlayPolicyBase):
    """
    Go AI policy using Monte Carlo Tree Search (see
    https://en.wikipedia.org/wiki/Monte_Carlo_tree_search)
    """

    async def __init__(self) -> None:
        self.tree: Optional[TreeNode] = None

    async def play(self, game: Game, color: Color) -> Optional[Action]:
        pass

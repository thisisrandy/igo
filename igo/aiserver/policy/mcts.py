from typing import Optional
from igo.game import Action, Color, Game
from igo.aiserver.policy.base import PlayPolicyBase


class MCTSPolicy(PlayPolicyBase):
    """
    Go AI policy using Monte Carlo Tree Search (see
    https://en.wikipedia.org/wiki/Monte_Carlo_tree_search)
    """

    async def __init__(self) -> None:
        pass

    async def play(self, game: Game, color: Color) -> Optional[Action]:
        pass

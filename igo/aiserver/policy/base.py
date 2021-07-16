"""
Abstract base class which all play policies must implement
"""

from abc import ABC, abstractmethod
from typing import Optional

from asyncinit import asyncinit
from igo.game import Action, Color, Game


@asyncinit
class PlayPolicyBase(ABC):
    @abstractmethod
    async def play(self, game: Game, color: Color) -> Optional[Action]:
        """
        If `color` is allowed to take an action, select one and return it.
        Otherwise, do any bookkeeping related to the last action taken and
        return None
        """

        raise NotImplementedError()

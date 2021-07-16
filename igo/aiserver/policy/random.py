from datetime import datetime
import logging
from typing import Optional
from igo.game import Action, ActionType, Color, Game
from igo.aiserver.policy.base import PlayPolicyBase
from random import choice


class RandomPolicy(PlayPolicyBase):
    """
    Play policy that makes random legal moves until there are none left and
    accepts all requests
    """

    async def play(self, game: Game, color: Color) -> Optional[Action]:
        ts = datetime.now().timestamp
        if game.pending_request:
            if game.pending_request.initiator is not color:
                logging.info(
                    f"Accepting {game.pending_request.initiator.name}'s request to"
                    f" {game.pending_request.request_type.name.replace('_', ' ')}"
                )
                return Action(ActionType.accept, color, ts)
        elif game.turn is color:
            choices = game.legal_moves(color)
            if not choices:
                logging.info("No legal moves found. Passing instead")
                return Action(ActionType.pass_turn, color, ts)

            move = choice(choices)
            logging.info(f"Placing stone at {move}")
            return Action(ActionType.place_stone, color, ts, move)

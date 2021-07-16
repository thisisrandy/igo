"""
This module is the client entrypoint, which should be triggered by `http_server`
via `await Client(...).start()`. See notes there for details
"""

import asyncio
import logging
from igo.gameserver.containers import (
    ActionResponseContainer,
    ErrorContainer,
    GameStatusContainer,
    JoinGameResponseContainer,
    OpponentConnectedContainer,
)
from igo.gameserver.messages import (
    IncomingMessageType,
    OutgoingMessage,
    OutgoingMessageType,
)
from igo.gameserver.constants import KEY, TYPE, AI_SECRET
import json
from tornado.options import define, options
from tornado.websocket import websocket_connect

define(
    "game_server_url",
    default="ws://localhost:8888/websocket",
    help="connect to the game server at this address",
    type=str,
)

ERROR_SLEEP_PERIOD = 2


class Client:
    def __init__(self, player_key: str, ai_secret: str) -> None:
        self.player_key = player_key
        self.ai_secret = ai_secret
        # for synchronization. if we need to resend a message due to game server
        # error, keep track of an id for the last message. if the id is
        # incremented before the last message can be resent, don't attempt to
        # resend
        self.last_message_id = 0

    async def start(self) -> None:
        self.connection = con = await websocket_connect(options.game_server_url)
        con.write_message(
            json.dumps(
                {
                    TYPE: IncomingMessageType.join_game.name,
                    KEY: self.player_key,
                    AI_SECRET: self.ai_secret,
                }
            )
        )
        response: OutgoingMessage = OutgoingMessage.deserialize(
            await con.read_message()
        )
        assert response.message_type is OutgoingMessageType.join_game_response
        data: JoinGameResponseContainer = response.data
        if not data.success:
            logging.warn(
                f"Failed to join game using player key {self.player_key} because"
                f" '{data.explanation}'"
            )
            return

        await self._message_consumer()

        logging.info(f"Shutting down connection for player key {self.player_key}")
        self.connection.close()

    async def _message_consumer(self) -> None:
        while True:
            message: OutgoingMessage = OutgoingMessage.deserialize(
                await self.connection.read_message()
            )
            logging.info(f"Received message of type {message.message_type}")

            if message.message_type is OutgoingMessageType.game_action_response:
                action_response: ActionResponseContainer = message.data
                if action_response.success:
                    logging.info(
                        f"Action for player key {self.player_key} was successful"
                    )
                else:
                    # AIs should only take legal actions, so this should only
                    # happen if we are preempted in the endgame. hence, it
                    # should be safe to ignore
                    logging.warn(
                        f"Action for player key {self.player_key} was unsuccessful"
                        f" because '{action_response.explanation}'"
                    )
            elif message.message_type is OutgoingMessageType.game_status:
                game_status: GameStatusContainer = message.data
                self.game = game_status.game
                # TODO: if its our turn or we're in the endgame, do stuff. if
                # the game is over, disconnect
            elif message.message_type is OutgoingMessageType.chat:
                logging.info("Received chat thread. Ignoring")
            elif message.message_type is OutgoingMessageType.opponent_connected:
                opp_conned: OpponentConnectedContainer = message.data
                logging.info(
                    "Received opponent"
                    f"{' not' if not opp_conned.opponent_connected else ''}"
                    " connected"
                )
                if not opp_conned.opponent_connected:
                    break
            elif message.message_type is OutgoingMessageType.error:
                error: ErrorContainer = message.data
                logging.warning(
                    f"Received error: '{error.exception}'. Sleeping for"
                    f" {ERROR_SLEEP_PERIOD} and resending last message"
                )
                last_message_id = self.last_message_id
                await asyncio.sleep(ERROR_SLEEP_PERIOD)
                if last_message_id == self.last_message_id:
                    logging.info("Resending last message")
                    await self.connection.write_message(self.last_message)
                else:
                    logging.info(
                        "In error handling, another action was taken before the last"
                        " could be resent. Discarding"
                    )

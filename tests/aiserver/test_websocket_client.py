from __future__ import annotations
from enum import Enum, auto
from igo.aiserver.policy.random import RandomPolicy
from igo.game import Color, Game, GameStatus
from igo.gameserver.containers import (
    GameStatusContainer,
    JoinGameResponseContainer,
    KeyContainer,
    OpponentConnectedContainer,
)
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from igo.aiserver.websocket_client import Client
import unittest
from unittest.mock import AsyncMock, patch
from igo.gameserver.constants import KEY, TYPE, AI_SECRET
from igo.gameserver.messages import (
    IncomingMessageType,
    OutgoingMessage,
    OutgoingMessageType,
)


class ConnectionActionType(Enum):
    read = auto()
    write = auto()


@dataclass
class ConnectionAction:
    action_type: ConnectionActionType
    expected_in: Optional[Dict] = None
    return_val: Optional[OutgoingMessage] = None


class MockWebsocketConnection:
    """
    An instance of this class is intended to be used as the return value of a
    mock of `tornado.websocket.websocket_connect`. The idea is to have an
    expected queue of actions that the object is initialized with. Then, as its
    read and write methods are called, it verifies that the next action in the
    queue is what is being requested and returns an appropriate response, if any.
    This allows us to simulate a remote game server that the AI server can talk
    back and forth to, allowing us to verify its read/response pattern
    """

    def __init__(
        self, test_case: unittest.TestCase, actions: List[ConnectionAction]
    ) -> None:
        self.test_case = test_case
        self.actions = actions
        self.action_idx = 0

    def append(self, action: ConnectionAction) -> None:
        self.actions.append(action)

    def extend(self, actions: List[ConnectionAction]) -> None:
        self.actions.extend(actions)

    def _assert_actions_left(self) -> None:
        self.test_case.assertGreater(
            len(self.actions),
            self.action_idx,
            "Tried to take more actions than were specified in the test",
        )

    async def read_message(self) -> str:
        self._assert_actions_left()
        action = self.actions[self.action_idx]
        self.action_idx += 1
        tc = self.test_case
        tc.assertIs(action.action_type, ConnectionActionType.read)
        tc.assertIsNotNone(action.return_val)
        return json.dumps(action.return_val.jsonifyable())

    async def write_message(self, message: str) -> None:
        self._assert_actions_left()
        action = self.actions[self.action_idx]
        self.action_idx += 1
        tc = self.test_case
        tc.assertIs(action.action_type, ConnectionActionType.write)
        tc.assertIsNotNone(action.expected_in)
        tc.assertEqual(json.dumps(action.expected_in), message)

    def close(self) -> None:
        pass


class TestWebSocketClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        """
        Patches `websocket_connect` and sets it up to return a mock connection
        with join game boilerplate defined. Tests should proceed by adding
        appropriate actions to `self.test_mock` and then running
        `self.run_client` as their final action. Note that the client is joined
        as the black player
        """

        # see https://tinyurl.com/2acdhnhy
        patcher = patch(
            "igo.aiserver.websocket_client.websocket_connect", new_callable=AsyncMock
        )
        self.addCleanup(patcher.stop)
        self.connect_mock = patcher.start()

        self.player_key = "0123456789"
        self.ai_secret = "9876543210"
        self.test_mock = MockWebsocketConnection(
            self,
            [
                ConnectionAction(
                    ConnectionActionType.write,
                    {
                        TYPE: IncomingMessageType.join_game.name,
                        KEY: self.player_key,
                        AI_SECRET: self.ai_secret,
                    },
                ),
                ConnectionAction(
                    ConnectionActionType.read,
                    return_val=OutgoingMessage(
                        OutgoingMessageType.join_game_response,
                        JoinGameResponseContainer(
                            True,
                            "success",
                            KeyContainer(
                                "1234554321", self.player_key, None, self.ai_secret
                            ),
                            Color.black,
                        ),
                    ),
                ),
            ],
        )
        self.connect_mock.return_value = self.test_mock


    async def run_client(self, append_opponent_disconnected: bool = True):
        """
        Create and start a client. This should be the last action that every
        test function takes. If `append_opponent_disconnected`, append an
        opponent disconnected message to the end of `self.test_mock`, which
        should always shut down a well-behaved client. If it is set to False, it
        is assumed that some other method, e.g. setting the game status to
        complete, has been employed to cause the client to exit. When neither of
        these is true, the client will wait forever and the test will as such
        not complete
        """

        if append_opponent_disconnected:
            self.test_mock.append(
                ConnectionAction(
                    ConnectionActionType.read,
                    return_val=OutgoingMessage(
                        OutgoingMessageType.opponent_connected,
                        OpponentConnectedContainer(False),
                    ),
                )
            )

        client: Client = await Client(self.player_key, self.ai_secret, RandomPolicy)
        await client.start()

    async def test_exit_on_complete(self):
        game = Game()
        game.status = GameStatus.complete
        self.test_mock.append(
            ConnectionAction(
                ConnectionActionType.read,
                return_val=OutgoingMessage(
                    OutgoingMessageType.game_status,
                    GameStatusContainer(game, 1.0),
                ),
            )
        )
        await self.run_client(False)

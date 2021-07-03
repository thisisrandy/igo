"""
Replays the sample game repeatedly from multiple processes to measure the
server's ability to scale
"""

from datetime import datetime
from containers import (
    ActionResponseContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
)
from typing import Dict
from messages import IncomingMessageType, OutgoingMessage, OutgoingMessageType
import pickle
from game import Action, Game, Color
from tornado.websocket import WebSocketClientConnection, websocket_connect
import json
from constants import ACTION_TYPE, COORDS, KEY, TYPE, VS, COLOR, SIZE, KOMI
import asyncio

SERVER_URL = "ws://localhost:8888/websocket"

with open("sample_game.bin", "rb") as reader:
    sample_game: Game = pickle.load(reader)


async def play_once() -> None:
    """
    Play the game once through in a single thread and record the total time
    taken
    """

    start_time = datetime.now()

    # our first task is to open two connections, create a new game with one, and
    # join that game with the other

    black: WebSocketClientConnection = await websocket_connect(SERVER_URL)
    await black.write_message(
        json.dumps(
            {
                TYPE: IncomingMessageType.new_game.name,
                VS: "human",
                COLOR: Color.black.name,
                SIZE: sample_game.board.size,
                KOMI: sample_game.komi,
            }
        )
    )
    response: OutgoingMessage = OutgoingMessage.deserialize(await black.read_message())
    assert response.message_type is OutgoingMessageType.new_game_response
    data: NewGameResponseContainer = response.data
    assert data.success
    keys: Dict[Color, str] = data.keys

    white: WebSocketClientConnection = await websocket_connect(SERVER_URL)
    await white.write_message(
        json.dumps({TYPE: IncomingMessageType.join_game.name, KEY: keys[Color.white]})
    )
    response = OutgoingMessage.deserialize(await white.read_message())
    assert response.message_type is OutgoingMessageType.join_game_response
    data: JoinGameResponseContainer = response.data
    assert data.success

    # before proceeding, drain the message queues. we expect black to have four
    # (new game status messages + opp conn'd from after white joined), and white
    # to have three (join game status messages)

    for _ in range(4):
        await black.read_message()
    for _ in range(3):
        await white.read_message()

    # now that the game is set up, start a consumer task for each player and
    # wait for both to finish

    black_consumer = asyncio.create_task(
        play_consumer(black, Color.black, keys[Color.black])
    )
    white_consumer = asyncio.create_task(
        play_consumer(white, Color.white, keys[Color.white])
    )
    await black_consumer
    await white_consumer

    # finally, close the connections and record the total time taken

    black.close()
    white.close()

    time_taken = datetime.now() - start_time

    print(
        f"Took {time_taken} to play the sample game"
        f" ({len(sample_game.action_stack)} actions taken)"
    )


async def play_consumer(
    player: WebSocketClientConnection, player_color: Color, key: str
) -> None:
    """
    Create a server message consumer that operates by reading the sample game
    action stack from beginning to end. If the next action is taken by this
    player's color, take it and then wait for/verify the response, and in either
    case, wait for/verify the type of the attendant status update before moving
    onto the next action in the stack. Returns when the game has been played
    through to the end
    """

    response: OutgoingMessage
    for i in range(len(sample_game.action_stack)):
        action: Action = sample_game.action_stack[i]
        if action.color is player_color:
            await player.write_message(
                json.dumps(
                    {
                        TYPE: IncomingMessageType.game_action.name,
                        KEY: key,
                        ACTION_TYPE: action.action_type.name,
                        COORDS: action.coords,
                    }
                )
            )
            response = OutgoingMessage.deserialize(await player.read_message())
            assert response.message_type is OutgoingMessageType.game_action_response
            data: ActionResponseContainer = response.data
            assert data.success

        response = OutgoingMessage.deserialize(await player.read_message())
        assert response.message_type is OutgoingMessageType.game_status


asyncio.run(play_once())

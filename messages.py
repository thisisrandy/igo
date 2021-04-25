from __future__ import annotations
from constants import ACTION_TYPE, COLOR, VS, KOMI, KEY, TYPE
from datetime import datetime
from enum import Enum, auto
import json
from typing import Dict, List
import logging
from tornado.websocket import WebSocketHandler


class IncomingMessageType(Enum):
    new_game = auto()
    join_game = auto()
    game_action = auto()

    @staticmethod
    def required_keys() -> Dict[IncomingMessageType, List[str]]:
        """Return a dictionary of IncomingMessageType: list of required keys
        in the data attribute of an IncomingMessage with that message_type"""

        return {
            IncomingMessageType.new_game: [VS, COLOR, KOMI],
            IncomingMessageType.join_game: [KEY],
            IncomingMessageType.game_action: [KEY, ACTION_TYPE, COLOR],
        }


class OutgoingMessageType(Enum):
    new_game_response = auto()
    join_game_response = auto()
    game_action_response = auto()
    game_status = auto()


class Message:
    """
    Base class for messages

    Attributes:

        websocket_handler: tornado.websocket.WebSocketHandler - the
        associated message handler for this websocket

        timestamp: the server time at which this message was created
    """

    def __init__(self, websocket_handler: WebSocketHandler) -> None:
        self.websocket_handler: WebSocketHandler = websocket_handler
        self.timestamp: float = datetime.now().timestamp()


class IncomingMessage(Message):
    """
    Container class for incoming messages

    Attributes:

        message_type: IncomingMessageType - the type of the message

        data: Dict[str, object] - a dictionary of the message data
    """

    def __init__(self, json_str: str, *args, **kwargs) -> None:
        self.data: Dict[str, object] = json.loads(json_str)
        self.message_type: IncomingMessage = IncomingMessageType[self.data[TYPE]]
        del self.data[TYPE]
        for rk in IncomingMessageType.required_keys()[self.message_type]:
            assert (
                rk in self.data
            ), f"Required key {rk} not found in incoming message {self.data}"

        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"IncomingMessage(messsage_type={self.message_type}" f", data={self.data})"
        )


def send_outgoing_message(
    message_type: OutgoingMessageType, data: object, websocket_handler: WebSocketHandler
) -> bool:
    """
    Send outgoing message and return True on success and False otherwise

    Arguments:

        message_type: OutgoingMessageType - the type of the message

        data: object - any object implementing the jsonifyable method

        websocket_handler: WebSocketHandler - the vehicle by which to send
        the message
    """

    msg = json.dumps({"message_type": message_type.name, "data": data.jsonifyable()})
    try:
        websocket_handler.write_message(msg)
        logging.info(f"Sent a message of type {message_type}")
        logging.debug(f"Message data: {msg}")
        return True
    except Exception as e:
        logging.warn(f"Failed send a message of type {message_type} with exception {e}")
        return False

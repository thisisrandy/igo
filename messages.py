from __future__ import annotations
from constants import ACTION_TYPE, COLOR, MESSAGE, SIZE, VS, KOMI, KEY, TYPE
from datetime import datetime
from enum import Enum, auto
import json
from typing import Dict, List, Any
import logging
from tornado.websocket import WebSocketHandler
from abc import ABC, abstractmethod


class IncomingMessageType(Enum):
    new_game = auto()
    join_game = auto()
    game_action = auto()
    chat_message = auto()

    @staticmethod
    def required_keys() -> Dict[IncomingMessageType, List[str]]:
        """Return a dictionary of IncomingMessageType: list of required keys
        in the data attribute of an IncomingMessage with that message_type"""

        return {
            IncomingMessageType.new_game: [VS, COLOR, SIZE, KOMI],
            IncomingMessageType.join_game: [KEY],
            IncomingMessageType.game_action: [KEY, ACTION_TYPE],
            IncomingMessageType.chat_message: [KEY, MESSAGE],
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

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False
        return (
            self.websocket_handler is o.websocket_handler
            and self.timestamp == o.timestamp
        )


class IncomingMessage(Message):
    """
    Container class for incoming messages

    Attributes:

        message_type: IncomingMessageType - the type of the message

        data: Dict[str, object] - a dictionary of the message data
    """

    def __init__(self, json_str: str, *args, **kwargs) -> None:
        self.data: Dict[str, object] = json.loads(json_str)
        self.message_type: IncomingMessageType = IncomingMessageType[self.data[TYPE]]
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

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False
        return (
            self.data == o.data
            and self.message_type == o.message_type
            and super().__eq__(o)
        )


class JsonifyableBase(ABC):
    """Base class for classes usable as OutgoingMessage data"""

    @abstractmethod
    def jsonifyable(self) -> Any:
        raise NotImplementedError()


async def send_outgoing_message(
    message_type: OutgoingMessageType,
    data: JsonifyableBase,
    websocket_handler: WebSocketHandler,
) -> bool:
    """
    Send outgoing message. Return True on success and False otherwise

    NOTE: This is a module method and not a class because conceptually,
    outgoing messages are meant to be sent immediately and not checked/routed
    through any components other that a WebSocketHandler. There is also a
    practical reason: I can't for the life of me figure out how to check how
    a constructor was called with the unittest library, so testing this as
    e.g. a class with an argumentless send method was proving difficult. Note
    that the method detailed e.g. at tinyurl.com/996jp3m, which uses the old
    mock library, is no longer valid

    Arguments:

        message_type: OutgoingMessageType - the type of the message

        data: JsonifyableBase - any object implementing the jsonifyable method

        websocket_handler: WebSocketHandler - the vehicle by which to send
        the message
    """

    msg = json.dumps({"message_type": message_type.name, "data": data.jsonifyable()})
    try:
        await websocket_handler.write_message(msg)
        logging.info(f"Sent a message of type {message_type}")
        logging.debug(f"Message data: {msg}")
        return True
    except Exception as e:
        logging.warning(
            f"Failed send a message of type {message_type} with exception {e}"
        )
        return False

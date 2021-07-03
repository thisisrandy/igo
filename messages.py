from __future__ import annotations
from chat import ChatThread
from containers import (
    ActionResponseContainer,
    ErrorContainer,
    GameStatusContainer,
    JoinGameResponseContainer,
    NewGameResponseContainer,
    OpponentConnectedContainer,
)
from constants import ACTION_TYPE, COLOR, MESSAGE, SIZE, VS, KOMI, KEY, TYPE
from datetime import datetime
from enum import Enum, auto
import json
from typing import Dict, List, Optional, Union
import logging
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from serialization import JsonifyableBase, JsonifyableBaseDataClass


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
    chat = auto()
    opponent_connected = auto()
    error = auto()


class Message:
    """
    Base class for messages

    Attributes:

        websocket_handler: tornado.websocket.WebSocketHandler - the
        associated message handler for this websocket

        timestamp: the server time at which this message was created
    """

    __slots__ = ("websocket_handler", "timestamp")

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

    __slots__ = ("message_type", "data")

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


class OutgoingMessage(JsonifyableBaseDataClass):
    """
    Serializable class containing outgoing message data and a method for sending
    it

    Attributes:

        message_type: OutgoingMessageType - the type of the message

        data: Union[JsonifyableBase, JsonifyableBaseDataClass] - any object
        implementing the jsonifyable method

        websocket_handler: Optional[WebSocketHandler] - the vehicle by which to
        send the message

    Serialization note: the `websocket_handler` attribute is not included during
    serialization and is thus not available for deserialization
    """

    message_type: OutgoingMessageType
    data: Union[JsonifyableBase, JsonifyableBaseDataClass]
    websocket_handler: Optional[WebSocketHandler] = None

    def jsonifyable(self) -> Dict:
        return {"messageType": self.message_type.name, "data": self.data.jsonifyable()}

    @classmethod
    def _deserialize(cls, data: Dict) -> OutgoingMessage:
        msg_type = OutgoingMessageType[data["messageType"]]
        raw_data = data["data"]
        if msg_type is OutgoingMessageType.new_game_response:
            deserialized_data = NewGameResponseContainer.deserialize(raw_data)
        elif msg_type is OutgoingMessageType.join_game_response:
            deserialized_data = JoinGameResponseContainer.deserialize(raw_data)
        elif msg_type is OutgoingMessageType.game_action_response:
            deserialized_data = ActionResponseContainer.deserialize(raw_data)
        elif msg_type is OutgoingMessageType.game_status:
            deserialized_data = GameStatusContainer.deserialize(raw_data)
        elif msg_type is OutgoingMessageType.chat:
            deserialized_data = ChatThread.deserialize(raw_data)
        elif msg_type is OutgoingMessageType.opponent_connected:
            deserialized_data = OpponentConnectedContainer.deserialize(raw_data)
        elif msg_type is OutgoingMessageType.error:
            deserialized_data = ErrorContainer.deserialize(raw_data)
        else:
            raise TypeError(
                f"Unrecognized outgoing message type {msg_type} encountered"
            )
        return OutgoingMessage(msg_type, deserialized_data)

    async def send(self) -> bool:
        """
        Write `self.jsonifyable()` to `self.websocket_handler`. Return True on
        success and False otherwise
        """

        assert (
            self.websocket_handler is not None
        ), "Cannot send outgoing messages without specifying a WebSocket"

        msg = json.dumps(self.jsonifyable())
        try:
            await self.websocket_handler.write_message(msg)
            logging.info(f"Sent a message of type {self.message_type}")
            logging.debug(f"Message data: {msg}")
            return True
        except WebSocketClosedError as e:
            # this is known to happen after a period of database inavailability and
            # appears to be harmless, so only issue a warning
            logging.warning(
                f"Failed send a message of type {self.message_type} because of"
                f" {e.__class__.__name__}"
            )
            return False

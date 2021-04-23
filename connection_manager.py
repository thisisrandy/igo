from __future__ import annotations
from constants import ACTION_TYPE, COLOR, VS, KOMI, KEY, TYPE
from datetime import datetime
from secrets import token_urlsafe
from dataclasses import dataclass
from enum import Enum, auto
import json
from typing import Dict, List
import logging
import tornado.websocket


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
    action_response = auto()
    game_status = auto()


class Message:
    """
    Base class for messages

    Attributes:

        websocket_handler: tornado.websocket.WebSocketHandler - the
        associated message handler for this websocket

        timestamp: the server time at which this message was created
    """

    def __init__(self, websocket_handler: tornado.websocket.WebSocketHandler) -> None:
        self.websocket_handler: tornado.websocket.WebSocketHandler = websocket_handler
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

        super(IncomingMessage, self).__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"IncomingMessage(messsage_type={self.message_type}" f", data={self.data})"
        )


class OutgoingMessage(Message):
    """
    Container class for outgoing messages

    Attributes:

        message_type: OutgoingMessageType - the type of the message

        data: object - any object implementing the jsonifyable method
    """

    def __init__(
        self, message_type: OutgoingMessageType, data: object, *args, **kwargs
    ) -> None:
        self.message_type: OutgoingMessageType = message_type
        self.data: object = data
        super(OutgoingMessage, self).__init__(*args, **kwargs)

    def _jsonify(self) -> str:
        return json.dumps(
            {"message_type": self.message_type, "data": self.data.jsonifyable()}
        )

    def send(self) -> None:
        try:
            self.websocket_handler.write_message(self._jsonify())
            logging.info(f"Sent a message of type {self.message_type}")
            logging.debug(f"Message details: {self}")
        except Exception as e:
            logging.warn(f"Failed send a message {self} with exception {e}")

    def __repr__(self) -> str:
        return (
            f"OutgoingMessage(message_type={self.message_type}"
            f", data={self.data}"
            f", timestamp={self.timestamp})"
        )


# TODO: All functionality below needs to be added. This is just a basic tornado
# websocket example as it stands

import tornado.web
import tornado.httpserver


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")
        print(self)

    def on_message(self, message):
        self.write_message("You said: " + message)

    def on_close(self):
        print("WebSocket closed")

    def check_origin(self, origin):
        return True


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/ws", EchoWebSocket)]
        settings = dict(
            cookie_secret=token_urlsafe(),
            xsrf_cookies=True,
        )
        super().__init__(handlers, **settings)


def main():
    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

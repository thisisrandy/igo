from __future__ import annotations
from secrets import token_urlsafe
from dataclasses import dataclass
from enum import Enum, auto
import json
from typing import Dict, List, Optional
import tornado.websocket

TYPE = "type"
KEY = "key"
VS = "vs"
COLOR = "color"
KOMI = "komi"


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
            # NOTE: this is obviously not exhaustive, but we handle game
            # actions at a different level, so check the message there
            IncomingMessageType.game_action: [KEY],
        }


class OutgoingMessageType(Enum):
    game_status = auto()


@dataclass
class Message:
    """
    Base class for messages

    Attributes:

        websocket_handler: tornado.websocket.WebSocketHandler - the
        associated message handler for this websocket
    """

    websocket_handler: tornado.websocket.WebSocketHandler


@dataclass
class IncomingMessage(Message):
    """
    Container class for incoming messages

    Attributes:

        message_type: Optional[MessageType] - the type of the message.
        Optional only to work as a @dataclass

        data: Optional[Dict[str, object]] - a dictionary of the message data.
        Optional only to work as a @dataclass
    """

    message_type: Optional[IncomingMessageType] = None
    data: Optional[Dict[str, object]] = None

    def __init__(self, json_str: str, *args, **kwargs) -> None:
        self.data = json.loads(json_str)
        self.message_type = IncomingMessageType[self.data[TYPE]]
        del self.data[TYPE]
        for rk in IncomingMessageType.required_keys()[self.message_type]:
            assert (
                rk in self.data
            ), f"Required key {rk} not found in incoming message {self.data}"

        super(IncomingMessage, self).__init__(*args, **kwargs)


@dataclass
class Response(Message):
    """
    Container class for outgoing responses to IncomingMessages. Distinct from
    OutgoingMessage, which the server initiates

    Attributes:

        success: bool - indicator of the associated IncomingMessage's success

        message: str - explanatory message
    """

    success: bool
    message: str


@dataclass
class OutgoingMessage(Message):
    """
    Container class for outgoing messages initiated by the server. Distinct
    from Response

    Attributes:

        message_type: OutgoingMessageType - the type of the message

        data: object - any object implementing the jsonifyable method
    """

    message_type: OutgoingMessageType
    data: object

    def jsonify(self) -> str:
        return json.dumps(
            {"message_type": self.message_type, "data": self.data.jsonifyable()}
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

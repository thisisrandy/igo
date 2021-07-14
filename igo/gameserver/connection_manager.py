from datetime import datetime
from functools import cached_property
import re
from .containers import ErrorContainer
from typing import Any, NoReturn
from tornado import httputil
from .messages import (
    IncomingMessage,
    OutgoingMessage,
    OutgoingMessageType,
)
from .game_manager import GameManager
from secrets import token_urlsafe
import logging
import tornado.web
import tornado.websocket
from tornado.options import define, options
import uvloop
import os
import urllib

# NOTE: tornado configures logging and provides some command line options by
# default.  See --help for details
define("port", default=8888, help="run on the given port", type=int)
define(
    "origin-suffix",
    default="",
    help=(
        "only allow connections originating from a domain ending in this value, e.g."
        " '.mydomain.com' to allow all subdomains of mydomain.com, or specify the"
        " empty string to allow all requests. begin with ^ to specify an exact match."
        " port number is not considered."
    ),
    type=str,
)


class IgoWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(
        self,
        application: tornado.web.Application,
        request: httputil.HTTPServerRequest,
        **kwargs: Any,
    ) -> None:
        assert hasattr(
            self, "game_manager"
        ), f"{self.__class__.__name__}.init must be called before use"
        super().__init__(application, request, **kwargs)

    @classmethod
    async def init(cls, origin_suffix: str):
        """
        Must be called before use. We want tornado to have priority setting
        up, so this is best called immediately before starting the event loop
        via tornado.ioloop.IOLoop.current().run_sync.

        To illustrate why, consider e.g. that logging may occur during
        GameManager set up. If we allow that to happen before calling
        tornado.options.parse_command_line, tornado's pretty logging will be
        preempted with the default logger settings
        """

        cls.game_manager: GameManager = await GameManager(os.environ["DATABASE_URL"])
        match_expr = (
            f"{'' if origin_suffix.startswith('^') else '.*'}{origin_suffix}(:\d+)?$"
        )
        cls.origin_matcher = re.compile(match_expr)
        logging.info(f"Restricting to origins matching {match_expr}")

    @cached_property
    def id(self):
        """
        Generates an id for this connection using our best guess of the client
        IP address + a truncated version of their websocket key
        """

        return (
            self.request.headers["X-Real-Ip"]
            if "X-Real-Ip" in self.request.headers
            else self.request.headers["X-Forwarded-For"]
            if "X-Forwarded-For" in self.request.headers
            else self.request.remote_ip
        ) + f" ({self.request.headers['Sec-Websocket-Key'][:7]})"

    def open(self):
        logging.info(f"New connection opened from {self.id}")

    async def on_message(self, json: str):
        start_time = datetime.now()
        logging.info(f"Received message from {self.id}: {json}")

        try:
            await self.game_manager.route_message(IncomingMessage(json, self))

        except Exception as e:
            logging.exception(f"Encountered exception while processing message {json}")
            await OutgoingMessage(
                OutgoingMessageType.error, ErrorContainer(e), self
            ).send()

        else:
            logging.info(
                f"Processed message {json} in"
                f" {(datetime.now() - start_time).total_seconds()}s"
            )

    def on_close(self):
        logging.info(f"Connection to {self.id} closed")
        tornado.ioloop.IOLoop.current().spawn_callback(
            lambda: self.game_manager.unsubscribe(self)
        )

    def check_origin(self, origin):
        parsed_origin = urllib.parse.urlparse(origin)
        if self.origin_matcher.match(parsed_origin.netloc):
            return True
        else:
            logging.warning(
                f"Disallowed origin {parsed_origin.netloc} attempted to connect"
            )

    def on_pong(self, data: bytes) -> None:
        logging.info(f"Received pong from {self.id}")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/websocket", IgoWebSocket)]
        settings = dict(
            cookie_secret=token_urlsafe(),
            xsrf_cookies=True,
            # note per the tornado docs that websocket_ping_timeout is the max
            # of 3 pings or 30 seconds by default, hence max(10*3, 30) = 30
            # seconds here. note also that heroku's idle timeout is 55 seconds
            websocket_ping_interval=10,
        )
        super().__init__(handlers, **settings)


def start_server() -> NoReturn:
    uvloop.install()
    options.parse_command_line()
    app = Application()
    app.listen(options.port)
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(lambda: IgoWebSocket.init(options.origin_suffix))
    logging.info(f"Listening on port {options.port}")
    io_loop.start()

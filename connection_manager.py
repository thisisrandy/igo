import re
from containers import ErrorContainer
from typing import Any
from tornado import httputil
from messages import IncomingMessage, OutgoingMessage, OutgoingMessageType
from game_manager import GameManager
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

    def open(self):
        logging.info("New connection opened")

    async def on_message(self, json: str):
        logging.info(f"Received message: {json}")
        try:
            await self.game_manager.route_message(IncomingMessage(json, self))
        except Exception as e:
            logging.exception(f"Encountered exception while processing message {json}")
            await OutgoingMessage(
                OutgoingMessageType.error, ErrorContainer(e), self
            ).send()

    def on_close(self):
        logging.info("Connection closed")
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


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/websocket", IgoWebSocket)]
        settings = dict(
            cookie_secret=token_urlsafe(),
            xsrf_cookies=True,
        )
        super().__init__(handlers, **settings)


def main():
    uvloop.install()
    options.parse_command_line()
    app = Application()
    app.listen(options.port)
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(lambda: IgoWebSocket.init(options.origin_suffix))
    logging.info(f"Listening on port {options.port}")
    io_loop.start()


if __name__ == "__main__":
    main()

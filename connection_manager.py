from typing import Any
from tornado import httputil
from messages import IncomingMessage
from game_manager import GameManager
from secrets import token_urlsafe
import logging
import tornado.web
import tornado.websocket
from tornado.options import define, options

# NOTE: tornado configures logging and provides some command line options by
# default.  See --help for details
define("port", default=8888, help="run on the given port", type=int)


class IgoWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(
        self,
        application: tornado.web.Application,
        request: httputil.HTTPServerRequest,
        **kwargs: Any,
    ) -> None:
        assert hasattr(
            self.__class__, "game_manager"
        ), f"{self.__class__.__name__}.init must be called before use"
        super().__init__(application, request, **kwargs)

    @classmethod
    def init(cls, game_manager: GameManager):
        """
        Must be called before use. We want tornado to have priority
        setting up, so this is best called immediately before starting the
        event loop.

        To illustrate why, consider e.g. that logging may occur during
        GameManager set up. If we allow that to happen before calling
        tornado.options.parse_command_line, tornado's pretty logging will be
        preempted with the default logger settings
        """

        cls.game_manager = game_manager

    def open(self):
        logging.info("New connection opened")

    def on_message(self, json: str):
        logging.info(f"Received message: {json}")
        self.__class__.game_manager.route_message(IncomingMessage(json, self))

    def on_close(self):
        logging.info("Connection closed")
        self.__class__.game_manager.unsubscribe(self)

    def check_origin(self, origin):
        # TODO: some sort of check here
        return True


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/websocket", IgoWebSocket)]
        settings = dict(
            cookie_secret=token_urlsafe(),
            xsrf_cookies=True,
        )
        super().__init__(handlers, **settings)


def main():
    options.parse_command_line()
    app = Application()
    app.listen(options.port)
    IgoWebSocket.init(GameManager())
    logging.info(f"Listening on port {options.port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

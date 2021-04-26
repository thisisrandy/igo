from messages import IncomingMessage
from game_manager import GameManager
from secrets import token_urlsafe
import logging
import tornado.web
import tornado.websocket
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("loglevel", default="info", help="set the logging level to this", type=str)


def _parse_log_level(string: str) -> int:
    string = string.lower()
    if string == "notset":
        return logging.NOTSET
    elif string == "debug":
        return logging.DEBUG
    elif string == "info":
        return logging.INFO
    elif string == "warn" or string == "warning":
        return logging.WARNING
    elif string == "error":
        return logging.ERROR
    elif string == "critical":
        return logging.CRITICAL
    else:
        raise ValueError(f"{string} is not a valid log level")


class IgoWebSocket(tornado.websocket.WebSocketHandler):
    game_manager = GameManager()

    def open(self):
        logging.info("New connection opened")

    def on_message(self, json: str):
        logging.info("Received message")
        logging.debug(f"Message details: {json}")
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
    logging.basicConfig(level=_parse_log_level(options.loglevel))
    app = Application()
    app.listen(options.port)
    logging.info(f"Listening on port {options.port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

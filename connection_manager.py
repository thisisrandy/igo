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
        handlers = [(r"/websocket", EchoWebSocket)]
        settings = dict(
            cookie_secret=token_urlsafe(),
            xsrf_cookies=True,
        )
        super().__init__(handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.basicConfig(level=_parse_log_level(options.loglevel))
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

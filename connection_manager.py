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
    game_manager = GameManager()

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
    logging.info(f"Listening on port {options.port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

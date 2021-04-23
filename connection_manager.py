from secrets import token_urlsafe
import logging

# TODO: All functionality below needs to be added. This is just a basic tornado
# websocket example as it stands

import tornado.web
import tornado.websocket


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
    logging.basicConfig(level=logging.INFO)
    main()

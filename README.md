## igo-backend

<p align="center"><img alt="igo screenshot" src="https://github.com/thisisrandy/igo-frontend/blob/main/screenshot.png" /></p>

This is the backend (game server) code for a browser-based
[igo](<https://en.wikipedia.org/wiki/Go_(game)>) (囲碁, go) application, which you
can play [here](#). The frontend (user interface) code is
[here](https://github.com/thisisrandy/igo-frontend).

### Installation

1. Clone the repository
2. Install [poetry](https://python-poetry.org/docs/)
3. Run `poetry install`

#### python version requirement

≥ 3.8

### Running locally

Run `poetry run connection_manager.py` from the root directory. You will also
need an instance of the [user
interface](https://github.com/thisisrandy/igo-frontend) running in order to
play.

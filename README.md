## igo-backend

<p align="center"><img alt="igo screenshot" src="https://github.com/thisisrandy/igo-frontend/blob/main/screenshot.png" /></p>

This is the backend (game server) code for a browser-based
[igo](<https://en.wikipedia.org/wiki/Go_(game)>) (囲碁, go) application, which you
can play [here](#). The frontend (user interface) code is
[here](https://github.com/thisisrandy/igo-frontend).

### Installation

1. Clone the repository
2. Create a [python virtual
   environment](https://docs.python.org/3/tutorial/venv.html) in the root directory
   and activate it
3. Run `pip install -r requirements.txt`

#### python version requirement

≥ 3.8

### Running locally

With your [virtual environment](https://docs.python.org/3/tutorial/venv.html)
activated, run `python connection_manager.py` from the root directory. You will
also need an instance of the [user
interface](https://github.com/thisisrandy/igo-frontend) running in order to
play.

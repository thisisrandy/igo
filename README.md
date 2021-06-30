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
4. If necessary, [install](https://www.postgresql.org/download/) PostgreSQL
5. [Create](https://www.postgresql.org/docs/current/sql-createdatabase.html) a
   new database or point the application to an existing one
6. In your chosen database, run all `.sql` files in the `sql/` directory,
   starting with `tables.sql`

#### python version requirement

≥ 3.8

#### PostgreSQL version requirement

13.3 tested, but all supported versions will likely work

### Running locally

Run `poetry run python connection_manager.py` from the root directory. You will
also need an instance of the [frontend
server](https://github.com/thisisrandy/igo-frontend) running in order to play.

### Technologies used

#### Production

- [aiofiles](https://github.com/Tinche/aiofiles) for reading local files
  asynchronously
- [asyncinit](https://github.com/kchmck/pyasyncinit) for writing `async`
  `__init__` methods
- [asyncpg](https://github.com/MagicStack/asyncpg) for performant, asynchronous
  communication with the PostgreSQL store
- [dataclassy](https://github.com/biqqles/dataclassy) for an
  auto-[slotting](https://docs.python.org/3/reference/datamodel.html?#object.__slots__)
  reimplementation of python
  [dataclasses](https://docs.python.org/3/library/dataclasses.html) that allows
  default attribute values and mutable defaults. `__slots__` is especially useful
  for classes with many instances being created and destroyed, e.g. the message
  containers that are used in this codebase
- [PostgreSQL](https://www.postgresql.org/) for a highly scalable store with
  asynchronous [pub/sub](https://www.postgresql.org/docs/current/sql-notify.html)
  capabilities for message passing
- [tornado](https://github.com/tornadoweb/tornado) for highly scalable,
  asynchronous [WebSockets](http://en.wikipedia.org/wiki/WebSocket) to communicate
  with the [frontend](https://github.com/thisisrandy/igo-frontend)

#### Development

- [black](https://github.com/psf/black) for formatting
- [coverage](https://coverage.readthedocs.io/) for code coverage
- [poetry](https://python-poetry.org/) for dependency and [virtual
  environment](https://docs.python.org/3/tutorial/venv.html) management
- [testing.postgresql](https://github.com/tk0miya/testing.postgresql) for
  testing with a live database

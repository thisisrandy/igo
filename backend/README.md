## backend

### Installation

1. Clone the repository
2. Install [poetry](https://python-poetry.org/docs/)
3. Run `poetry install` in the `backend` directory
4. If necessary, [install](https://www.postgresql.org/download/) PostgreSQL
5. [Create](https://www.postgresql.org/docs/current/sql-createdatabase.html) a
   new database. If desired, an existing database can also be used, provided there
   are no name conflicts with this application, though this is not recommended
6. In your chosen database, run all `.sql` files in the `sql/` directory,
   starting with `tables.sql`
7. Wherever the environment for the desired user is configured, set the
   `DATABASE_URL` variable to the [connection
   URI](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
   for your database. Note that `DATABASE_URL` follows the variable used in
   [heroku
   applications](https://devcenter.heroku.com/articles/heroku-postgresql#connecting-in-python)

**NOTE**: If the server is handling a large number of simultaneous connections,
it will be limited by the system open file limit, which may be set to a small
value by default on your system. If you are exceeding the limit, you will see
error messages like the following:

```
OSError: [Errno 24] Too many open files
```

You can check the current value on linux with `ulimit -n` and set it for the
current session with <code>ulimit -n <i>limit</i></code>, up to any limits
described in `/etc/security/limits.conf`. See [this
page](https://www.tecmint.com/increase-set-open-file-limits-in-linux/) for
additional details.

**NOTE**: As database connections are made via TCP/IP, a password is
required for all users by default. If you intend to connect without a password,
you must edit `pg_hba.conf` to trust the desired user on the loopback address by
adding a line like

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    my_db           postgres        127.0.0.1/32            trust
```

If you don't know the location of `pg_hba.conf`, connect to the database and run
`show hba_file;`

#### python version requirement

≥ 3.9

#### PostgreSQL version requirement

13.3 tested, but all supported versions will likely work

### Running locally

Run `poetry run python -m igo.gameserver` from the root directory. If running
the AI server, separately run `poetry run python -m igo.aiserver`. Use the
`--help` option on either for additional options. You will also need an instance
of the [frontend server](../frontend/README.md) running in order to play.

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
  asynchronous [WebSockets](http://en.wikipedia.org/wiki/WebSocket) to
  communicate with the [frontend](https://github.com/thisisrandy/igo-frontend)
  and between the game and AI servers
- [uvloop](https://github.com/MagicStack/uvloop) for improved `asyncio`
  performance

#### Development

- [black](https://github.com/psf/black) for formatting
- [coverage](https://coverage.readthedocs.io/) for code coverage
- [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile) for
  performance analysis
- [iPython](https://ipython.org/) for interactive exploration and testing
- [numpy](https://numpy.org/) for performance test result munging
- [poetry](https://python-poetry.org/) for dependency and [virtual
  environment](https://docs.python.org/3/tutorial/venv.html) management
- [testing.postgresql](https://github.com/tk0miya/testing.postgresql) for
  testing with a live database

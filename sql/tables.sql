DROP TABLE IF EXISTS game, player_key, chat CASCADE;

CREATE TABLE game (
  id serial PRIMARY KEY,
  data bytea NOT NULL,
  version integer NOT NULL DEFAULT 0,
  players_connected integer NOT NULL DEFAULT 0,
  -- in seconds
  time_played double precision NOT NULL DEFAULT 0.0,
  -- unix time, set when loaded if not already loaded elsewhere and whenever
  -- written, unset when last client unsubs
  write_load_timestamp double precision DEFAULT null
);

CREATE TABLE player_key (
  key char(10) PRIMARY KEY,
  game_id integer REFERENCES game(id)
    -- this allows us to easily delete games and wipe out their player key rows
    -- as well
    ON DELETE CASCADE
    NOT NULL,
  color char(5) NOT NULL,
  opponent_key char(10)
    REFERENCES player_key(key)
    -- mutually referential keys are added in pairs when creating a
    -- new game. as such, the foreign key check needs to be deferred
    -- inside transactions
    DEFERRABLE INITIALLY DEFERRED
    NOT NULL,
  managed_by char(64)
);

CREATE TABLE chat (
  id serial PRIMARY KEY,
  timestamp double precision NOT NULL,
  color char(5) NOT NULL,
  message text NOT NULL,
  game_id integer REFERENCES game(id)
    -- as in player_key, we want game deletions to cascade to chat deletions
    ON DELETE CASCADE
    NOT NULL
);

CREATE TABLE IF NOT EXISTS game (
  id serial PRIMARY KEY,
  data bytea NOT NULL,
  version integer NOT NULL
);

CREATE TABLE IF NOT EXISTS player_key (
  key char(10) PRIMARY KEY,
  game_id integer REFERENCES game(id) NOT NULL,
  color char(5) NOT NULL,
  -- mutually referential keys are added in pairs when creating a
  -- new game. as such, the foreign key check needs to be deferred
  -- inside transactions
  opponent_key char(10) REFERENCES player_key(key) DEFERRABLE INITIALLY DEFERRED NOT NULL,
  managed_by char(64)
);

CREATE TABLE IF NOT EXISTS chat (
  id serial PRIMARY KEY,
  timestamp real NOT NULL,
  color char(5) NOT NULL,
  message text NOT NULL,
  game_id integer REFERENCES game(id)
);

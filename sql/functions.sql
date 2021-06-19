CREATE OR REPLACE FUNCTION join_game(
  key_to_join char(10),
  manager_id char(64)
)
  RETURNS TABLE (
    result text,
    white_key char(10),
    black_key char(10)
  )
  LANGUAGE plpgsql
AS
$$
DECLARE
  other_connected boolean;
BEGIN
  SELECT managed_by IS NOT NULL
  INTO other_connected
  FROM player_key
  WHERE key = key_to_join
  FOR UPDATE;

  if not found then
    -- NOTE: null apparently registers as type text without an explicit cast,
    -- which then causes an error about the return type not matching the
    -- declared type, hence the casts here and below
    RETURN QUERY SELECT 'dne', null::char(10), null::char(10);
  elsif other_connected then
    RETURN QUERY SELECT 'in_use', null::char(10), null::char(10);
  else
    UPDATE player_key
    SET managed_by = manager_id
    WHERE key = key_to_join;

    PERFORM pg_notify((
      SELECT CONCAT('opponent_connected_', opponent_key)
      FROM player_key
      WHERE key = key_to_join
      ), 'true');

    RETURN QUERY
      SELECT
        'success'
        , CASE WHEN color = 'white' THEN key ELSE opponent_key END
        , CASE WHEN color = 'black' THEN key ELSE opponent_key END
      FROM player_key
      WHERE key = key_to_join;
  end if;

  RETURN;
END $$;

CREATE OR REPLACE FUNCTION write_game(
  key_to_write char(10),
  data_to_write bytea,
  version_to_write integer
)
  RETURNS boolean
  LANGUAGE plpgsql
AS
$$
BEGIN
  UPDATE game
  SET data = data_to_write, version = version_to_write
  WHERE version = version_to_write-1 AND id = (
    SELECT game_id
    FROM player_key
    WHERE key = key_to_write
  );

  if found then
    PERFORM pg_notify((
      SELECT CONCAT('game_status_', opponent_key)
      FROM player_key
      WHERE key = key_to_write
    ), '');

    RETURN true;
  end if;

  RETURN false;
END $$;

CREATE OR REPLACE FUNCTION unsubscribe(
  key_to_unsubscribe char(10),
  currently_managed_by char(64)
)
  RETURNS boolean
  LANGUAGE plpgsql
AS
$$
DECLARE
  channel text;
BEGIN
  UPDATE player_key
  SET managed_by = null
  WHERE key = key_to_unsubscribe
    and managed_by = currently_managed_by;

  if found then
    PERFORM pg_notify((
      SELECT CONCAT('opponent_connected_', opponent_key)
      FROM player_key
      WHERE key = key_to_unsubscribe
      ), 'false');

    RETURN true;
  end if;

  RETURN false;
END $$;

CREATE OR REPLACE FUNCTION write_chat(
  msg_timestamp real,
  msg_text text,
  author_key char(10)
)
  RETURNS boolean
  LANGUAGE plpgsql
AS
$$
DECLARE
  target_game_id integer;
  author_color char(5);
BEGIN
  SELECT game_id, color
  FROM player_key
  WHERE key = author_key
  INTO target_game_id, author_color;

  if target_game_id is null then
    RETURN false;
  end if;

  INSERT INTO chat (timestamp, color, message, game_id)
  VALUES (msg_timestamp, author_color, msg_text, target_game_id);

  -- we notify ourselves here because new infomation (the row id) has been added
  -- during the insertion process, and also because our opponent could have
  -- added one or more messages while we were adding this one. it's much cleaner
  -- to instruct the game server to go to the db to get in order messages rather
  -- than trying to work it out from several sources. this is in contrast to
  -- game updates, where we know that if we successfully wrote our update, it is
  -- in fact the latest version, so there's no need to go back to the db to
  -- uselessly read in what we just wrote out
  PERFORM pg_notify((SELECT CONCAT('chat_', author_key)), '');
  PERFORM pg_notify((
      SELECT CONCAT('chat_', opponent_key)
      FROM player_key
      WHERE key = author_key
  ), '');

  RETURN true;
END $$;

CREATE OR REPLACE FUNCTION get_game_status(
  associated_player_key char(10)
)
  RETURNS TABLE (
    game_data bytea,
    version integer
  )
  LANGUAGE plpgsql
AS
$$
BEGIN
  RETURN QUERY
    SELECT g.data, g.version
    FROM game g, player_key pk
    WHERE pk.key = associated_player_key
      AND pk.game_id = g.id;

  if not found then
    raise 'Game associated with player key % not found', associated_player_key;
  end if;

  RETURN;
END $$;

CREATE OR REPLACE FUNCTION get_chat_updates(
  associated_player_key char(10),
  last_id integer DEFAULT -1
)
  RETURNS TABLE (
    id integer,
    time_stamp real,
    color char(5),
    message text
  )
  LANGUAGE plpgsql
AS
$$
BEGIN
  PERFORM 1
  FROM player_key
  WHERE key = associated_player_key;

  if not found then
    raise 'Player key % not found', associated_player_key;
  end if;

  RETURN QUERY
    SELECT c.id, c.timestamp, c.color, c.message
    FROM chat c, player_key pk
    WHERE pk.key = associated_player_key
      AND pk.game_id = c.game_id
      AND c.id > last_id
    ORDER BY c.id;

  -- NOTE: having the above return nothing is a perfectly normal occurence when
  -- we join a game with no chat messages, so no need to raise any exceptions if
  -- nothing is found

  RETURN;
END $$;

CREATE OR REPLACE FUNCTION get_opponent_connected(
  my_player_key char(10)
)
  RETURNS boolean
  LANGUAGE plpgsql
AS
$$
DECLARE
  opponent_connected boolean;
BEGIN
  SELECT op.managed_by is not null
  INTO opponent_connected
  FROM player_key self, player_key op
  WHERE self.key = my_player_key
    AND self.opponent_key = op.key;

  if not found then
    raise 'Player key % not found', my_player_key;
  end if;

  RETURN opponent_connected;
END $$;
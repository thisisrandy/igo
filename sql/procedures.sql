CREATE OR REPLACE PROCEDURE new_game(
  IN game_data bytea,
  IN key_w char(10),
  IN key_b char(10),
  -- provide these args to join a player to the game
  IN player_color char(5) DEFAULT null,
  IN managed_by char(64) DEFAULT null
)
  LANGUAGE plpgsql
AS $$
DECLARE
    new_id game.id%TYPE;
BEGIN
    INSERT INTO game (data, version)
    VALUES (game_data, 0)
    RETURNING id
    INTO new_id;

    INSERT INTO player_key
    VALUES (key_w, new_id, 'white', COALESCE(player_color = 'white', false), key_b,
      CASE WHEN player_color = 'white' THEN managed_by ELSE null END);

    INSERT INTO player_key
    VALUES (key_b, new_id, 'black', COALESCE(player_color = 'black', false), key_w,
      CASE WHEN player_color = 'black' THEN managed_by ELSE null END);

    COMMIT;
END; $$

CREATE OR REPLACE FUNCTION join_game(
  key_to_join char(10),
  manager_id char(64)
)
  RETURNS text
  LANGUAGE plpgsql
AS
$$
DECLARE
  other_connected player_key.connected%TYPE;
BEGIN
  SELECT connected
  INTO other_connected
  FROM player_key
  WHERE key = key_to_join
  FOR UPDATE;

  if other_connected is null then
    RETURN 'dne';
  elsif other_connected then
    RETURN 'in_use';
  else
    UPDATE player_key
    SET connected = true, managed_by = manager_id
    WHERE key = key_to_join;

    RETURN 'success';
  end if;
END; $$

CREATE OR REPLACE FUNCTION write_game(
  key_to_write char(10),
  data_to_write bytea,
  version_to_write integer
)
  RETURNS boolean
  LANGUAGE plpgsql
AS
$$
DECLARE
  update_count integer;
BEGIN
  UPDATE game
  SET data = data_to_write, version = version_to_write
  WHERE version = version_to_write-1 AND id = (
    SELECT game_id
    FROM player_key
    WHERE key = key_to_write
  );

  GET DIAGNOSTICS update_count := ROW_COUNT;

  if update_count = 1 then
    PERFORM pg_notify((
      SELECT CONCAT('game_status_', opponent_key)
      FROM player_key
      WHERE key = key_to_write
    ), '');

    RETURN true;
  end if;

  RETURN false;
END; $$
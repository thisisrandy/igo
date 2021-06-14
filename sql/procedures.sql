CREATE OR REPLACE PROCEDURE do_cleanup(
  manager_id char(64)
)
  LANGUAGE plpgsql
AS
$$
BEGIN
  UPDATE player_key
  SET managed_by = null
  WHERE managed_by = manager_id;
END; $$

CREATE OR REPLACE PROCEDURE new_game(
  game_data bytea,
  key_w char(10),
  key_b char(10),
  -- provide these args to join a player to the game
  player_color char(5) DEFAULT null,
  manager_id char(64) DEFAULT null
)
  LANGUAGE plpgsql
AS
$$
DECLARE
  new_id game.id%TYPE;
BEGIN
  INSERT INTO game (data, version)
  VALUES (game_data, 0)
  RETURNING id
  INTO new_id;

  INSERT INTO player_key
  VALUES (key_w, new_id, 'white', key_b,
    CASE WHEN player_color = 'white' THEN manager_id ELSE null END);

  INSERT INTO player_key
  VALUES (key_b, new_id, 'black', key_w,
    CASE WHEN player_color = 'black' THEN manager_id ELSE null END);
END; $$

CREATE OR REPLACE PROCEDURE trigger_update_all(
  key_to_notify char(10)
)
  LANGUAGE plpgsql
AS
$$
BEGIN
  PERFORM pg_notify((SELECT CONCAT('game_status_', key_to_notify)), '');
  PERFORM pg_notify((SELECT CONCAT('chat_', key_to_notify)), '');
  PERFORM pg_notify((SELECT CONCAT('opponent_connected_', key_to_notify)), '');
END; $$
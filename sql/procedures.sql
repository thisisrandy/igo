CREATE OR REPLACE PROCEDURE new_game(
  IN game_data bytea,
  IN key_w char(10),
  IN key_b char(10),
  -- provide these args to join a player to the game
  IN player_color char(5) DEFAULT null,
  IN managed_by char(64) DEFAULT null
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
      CASE WHEN player_color = 'white' THEN managed_by ELSE null END);

    INSERT INTO player_key
    VALUES (key_b, new_id, 'black', key_w,
      CASE WHEN player_color = 'black' THEN managed_by ELSE null END);

    COMMIT;
END; $$
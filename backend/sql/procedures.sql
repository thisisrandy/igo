CREATE OR REPLACE PROCEDURE do_cleanup(
  manager_id char(64)
)
  LANGUAGE plpgsql
AS
$$
DECLARE
  gid integer;
BEGIN
  for gid in SELECT game_id
              FROM player_key
              WHERE managed_by = manager_id
              FOR UPDATE
  loop
    UPDATE game
    SET players_connected = players_connected - 1
      , write_load_timestamp =
          CASE WHEN players_connected = 1
          THEN null
          ELSE write_load_timestamp
          END
    WHERE id = gid;
  end loop;

  UPDATE player_key
  SET managed_by = null
  WHERE managed_by = manager_id;
END $$;

CREATE OR REPLACE PROCEDURE new_game(
  game_data bytea,
  key_w char(10),
  key_b char(10),
  -- provide these args to join a player to the game
  player_color char(5) DEFAULT null,
  manager_id char(64) DEFAULT null,
  -- optionally unsubscribe before creating new game
  key_to_unsubscribe char(10) DEFAULT null,
  -- optionally provide an AI secret for one or both keys
  ai_secret_w char(10) DEFAULT null,
  ai_secret_b char(10) DEFAULT null
)
  LANGUAGE plpgsql
AS
$$
DECLARE
  new_id game.id%TYPE;
BEGIN
  if player_color is not null then
    if player_color = 'white' and ai_secret_w is not null or
      player_color = 'black' and ai_secret_b is not null then
        raise 'Cannot assign an AI secret to the specified player color (%)', player_color;
    end if;
  end if;

  if key_to_unsubscribe is not null then
    if not (SELECT * FROM unsubscribe(key_to_unsubscribe, manager_id)) then
      raise 'Prior to create new game, failed to unsubscribe from % managed by %',
        key_to_unsubscribe, manager_id;
    end if;
  end if;

  INSERT INTO game (data, players_connected, write_load_timestamp)
  VALUES (
    game_data
    , CASE WHEN player_color IS NOT null THEN 1 ELSE 0 END
    , CASE WHEN player_color IS NOT null THEN extract(epoch from now()) ELSE null END
    )
  RETURNING id
  INTO new_id;

  INSERT INTO player_key
  VALUES (key_w, new_id, 'white', key_b,
    CASE WHEN player_color = 'white' THEN manager_id ELSE null END, ai_secret_w);

  INSERT INTO player_key
  VALUES (key_b, new_id, 'black', key_w,
    CASE WHEN player_color = 'black' THEN manager_id ELSE null END, ai_secret_b);
END $$;

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
END $$;
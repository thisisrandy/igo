-- needed for cleanup
DROP INDEX IF EXISTS player_key_managed_by_index;
CREATE INDEX player_key_managed_by_index ON player_key(managed_by);
-- needed for getting chat updates
DROP INDEX IF EXISTS chat_id_game_id_index;
CREATE INDEX chat_id_game_id_index ON chat(game_id, id);


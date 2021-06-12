-- needed for cleanup
CREATE INDEX IF NOT EXISTS player_key_managed_by_index ON player_key(managed_by);
-- needed for getting chat updates
CREATE INDEX IF NOT EXISTS chat_id_game_id_index ON chat(game_id, id);


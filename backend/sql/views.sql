CREATE OR REPLACE VIEW chat_parsed_time AS
SELECT id, to_timestamp(timestamp) AS parsed_timestamp, color, message, game_id
FROM chat;

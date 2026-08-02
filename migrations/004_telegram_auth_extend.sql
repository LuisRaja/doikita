-- Run this SQL in your Supabase SQL Editor if you already ran 002_telegram_auth.sql
-- It adds the mode and chat_id columns used to persist Telegram auth across restarts.

ALTER TABLE telegram_auth ADD COLUMN IF NOT EXISTS mode TEXT;
ALTER TABLE telegram_auth ADD COLUMN IF NOT EXISTS chat_id BIGINT;

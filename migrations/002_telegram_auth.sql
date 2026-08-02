-- Run this SQL in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS telegram_auth (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    mode TEXT,
    chat_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE telegram_auth ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all on telegram_auth" ON telegram_auth FOR ALL USING (true) WITH CHECK (true);

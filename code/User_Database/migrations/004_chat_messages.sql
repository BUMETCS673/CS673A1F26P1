-- AI-USAGE SUMMARY
-- Authors: Daniel Winnie
-- Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
-- Overall AI Contribution: ~90%
-- AI-Assisted Areas: chat_messages table (FV-121)
-- Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
-- Notes/Verification: applied by start_project.sh and the PR checks workflow; tests/live_chat_history.py

-- FV-121: one row per chat exchange (the user's request and the assistant's reply).
-- `reply` stores what the parser understood and the matched event IDs, never the
-- rendered text, so cards are rebuilt from current catalog data when history loads.
-- Deleting a user also deletes their chat history.
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_text VARCHAR(1000) NOT NULL,
    reply JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- History is always read "newest N for one user", so index exactly that.
CREATE INDEX IF NOT EXISTS chat_messages_user_id_idx ON chat_messages (user_id, id DESC);

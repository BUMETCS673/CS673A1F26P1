-- AI-USAGE SUMMARY
-- Authors: Daniel Winnie
-- Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
-- Overall AI Contribution: ~90%
-- AI-Assisted Areas: user_sessions table
-- Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
-- Notes/Verification: applied by start_project.sh; tests/live_auth.py

-- Login sessions for the auth API. Only a SHA-256 hash of each browser token is
-- stored, so reading this table does not reveal usable session cookies.
CREATE TABLE IF NOT EXISTS user_sessions (
    token_hash CHAR(64) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS user_sessions_user_id_idx ON user_sessions (user_id);

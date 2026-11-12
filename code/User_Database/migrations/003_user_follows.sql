-- AI-USAGE SUMMARY
-- Authors: Yuchen Xu (feature requirements)
-- Tools: OpenAI Codex
-- Overall AI Contribution: Codex drafted this migration.
-- AI-Assisted Areas: PostgreSQL schema, constraints, and index.
-- Human Contributions: Yuchen Xu confirmed the one-way follow model.
-- Notes/Verification: tests/live_follows.py exercises the schema through the API.

CREATE TABLE IF NOT EXISTS user_follows (
    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    followed_id INTEGER NOT NULL,
    PRIMARY KEY (follower_id, followed_id),
    CONSTRAINT user_follows_followed_id_fkey
        FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT user_follows_no_self_follow CHECK (follower_id <> followed_id)
);

CREATE INDEX IF NOT EXISTS user_follows_followed_id_idx ON user_follows (followed_id);

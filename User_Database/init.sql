-- AI-USAGE SUMMARY
-- Authors: Daniel Winnie, Yuchen Xu (FV-113 account fields)
-- Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (user_sessions table); Yuchen Xu: not yet reported by the author - author to confirm in the AIUsageLog
-- Overall AI Contribution: ~85% (Daniel's parts); Yuchen Xu's part to be confirmed
-- AI-Assisted Areas: users table, sample rows, comments
-- Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep; Yuchen Xu: display_name / password_hash / activity_preferences columns
-- Notes/Verification: database initialised from an empty volume via start_project.sh; /api/health/database ok

-- This file runs automatically on the FIRST startup with an empty data volume.
-- It creates one table: a collection of rows with the same named columns.
CREATE TABLE users (
    -- PostgreSQL automatically assigns a different ID to each new user.
    -- PRIMARY KEY means this value uniquely identifies the row.
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- VARCHAR limits text length. NOT NULL requires a value.
    -- UNIQUE prevents two rows from using the exact same value.
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,

    -- FV-113: Added account fields for future registration.
    -- AI usage: ChatGPT helped with SQL syntax and field definitions.
    display_name VARCHAR(100),
    password_hash TEXT,
    activity_preferences TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[]
);

-- Login sessions (same as migrations/002_user_sessions.sql). Only a hash of each
-- browser token is stored. Deleting a user also deletes their sessions.
CREATE TABLE user_sessions (
    token_hash CHAR(64) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX user_sessions_user_id_idx ON user_sessions (user_id);

-- Two fictional placeholders so everyone can try viewing and editing rows.
-- Leave out id: PostgreSQL fills it in for us.
INSERT INTO users (username, email)
VALUES
    ('sample_alex', 'alex@example.com'),
    ('sample_sam', 'sam@example.com');

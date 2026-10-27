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

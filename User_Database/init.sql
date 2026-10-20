-- This file runs automatically on the FIRST startup with an empty data volume.
-- It creates one table: a collection of rows with the same named columns.
CREATE TABLE users (
    -- PostgreSQL automatically assigns a different ID to each new user.
    -- PRIMARY KEY means this value uniquely identifies the row.
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- VARCHAR limits text length. NOT NULL requires a value.
    -- UNIQUE prevents two rows from using the exact same value.
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- Two fictional placeholders so everyone can try viewing and editing rows.
-- Leave out id: PostgreSQL fills it in for us.
INSERT INTO users (username, email)
VALUES
    ('sample_alex', 'alex@example.com'),
    ('sample_sam', 'sam@example.com');

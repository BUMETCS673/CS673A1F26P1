-- AI-USAGE SUMMARY
-- Authors: Yuchen Xu
-- Tools: ChatGPT (OpenAI)
-- Overall AI Contribution: Moderate
-- AI-Assisted Areas: PostgreSQL syntax, account-field migration (FV-113), SQL testing commands, Git/GitHub workflow, and README documentation
-- Human Contributions: Yuchen Xu: edited SQL files, executed and tested the migration, verified database records, and committed changes to GitHub
-- Notes/Verification: migration run twice on an existing database; both sample users and their original IDs preserved; new account fields verified in PostgreSQL

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS display_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS activity_preferences TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];

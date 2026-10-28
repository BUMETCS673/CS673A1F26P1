-- AI-USAGE SUMMARY
-- Authors: Yuchen Xu
-- Tools: not yet reported by the author - author to confirm in the AIUsageLog
-- Overall AI Contribution: to be confirmed by Yuchen Xu
-- AI-Assisted Areas: account-field migration (FV-113)
-- Human Contributions: Yuchen Xu: migration design and testing
-- Notes/Verification: migration run twice on an existing database, sample users kept (per SDD 10.6)


ALTER TABLE users
    ADD COLUMN IF NOT EXISTS display_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS activity_preferences TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];

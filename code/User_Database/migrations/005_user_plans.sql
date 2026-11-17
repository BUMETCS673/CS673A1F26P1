-- AI-USAGE SUMMARY
-- Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
-- Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
-- Overall AI Contribution: ~90%
-- AI-Assisted Areas: user_plans table (FV-95)
-- Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
-- Notes/Verification: applied by start_project.sh and the PR checks workflow; tests/live_plans.py

-- FV-95: the events each user saved to My Plans. Events live in the Python catalog,
-- so only the event's stable ID is stored; the details are looked up when listing.
-- The primary key makes saving the same event twice impossible, and deleting a user
-- also deletes their plans.
CREATE TABLE IF NOT EXISTS user_plans (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id VARCHAR(100) NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, event_id)
);

-- "Which friends are going to this event?" looks plans up by event.
CREATE INDEX IF NOT EXISTS user_plans_event_id_idx ON user_plans (event_id);

# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: parameterized PostgreSQL queries for chat history (FV-121)
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/live_chat_history.py (two accounts, real database)

"""Database operations for each user's chat history. Every query filters by user_id,
so one account can never read or delete another account's messages."""

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.database import get_connection

HISTORY_LIMIT = 50


def save_exchange(user_id: int, request_text: str, interpretation: dict, event_ids: list[str]) -> None:
    """Store one request and the structured reply (parser output and event IDs)."""
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO chat_messages (user_id, request_text, reply) VALUES (%s, %s, %s)",
            (user_id, request_text, Jsonb({"interpretation": interpretation, "event_ids": event_ids})),
        )


def list_recent(user_id: int, limit: int = HISTORY_LIMIT) -> list[dict]:
    """The user's most recent exchanges, oldest first (the order the chat shows them)."""
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT id, request_text, reply, created_at FROM ("
            "  SELECT id, request_text, reply, created_at FROM chat_messages"
            "  WHERE user_id = %s ORDER BY id DESC LIMIT %s"
            ") AS recent ORDER BY id",
            (user_id, limit),
        )
        return cursor.fetchall()


def clear(user_id: int) -> None:
    """Delete every message of this user only."""
    with get_connection() as connection:
        connection.execute("DELETE FROM chat_messages WHERE user_id = %s", (user_id,))

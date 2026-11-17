# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: parameterized PostgreSQL queries for My Plans (FV-95) and friends going (mutual follows only)
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/live_plans.py (two accounts, real database)

"""Database operations for My Plans. Every query filters by user_id, so one account
can never read or change another account's plans."""

from psycopg.rows import dict_row

from app.database import get_connection


def list_saved(user_id: int) -> list[dict]:
    """The user's saved event IDs with when each was saved, oldest first."""
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT event_id, saved_at FROM user_plans WHERE user_id = %s ORDER BY saved_at, event_id",
            (user_id,),
        )
        return cursor.fetchall()


def save(user_id: int, event_id: str) -> None:
    """Save an event. Saving it again changes nothing (and keeps the first saved_at)."""
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO user_plans (user_id, event_id) VALUES (%s, %s) "
            "ON CONFLICT (user_id, event_id) DO NOTHING",
            (user_id, event_id),
        )


def remove(user_id: int, event_id: str) -> None:
    """Remove an event from this user's plans only. Removing it again changes nothing."""
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM user_plans WHERE user_id = %s AND event_id = %s",
            (user_id, event_id),
        )


# Friends going: a "friend" is a mutual follow (each follows the other). Both queries
# check that in SQL at request time, so unfollowing removes access immediately.

def friends_going(user_id: int, event_id: str) -> list[dict]:
    """Mutual follows of this user who saved this event, by username."""
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT u.id, u.username, u.display_name FROM user_plans AS p "
            "JOIN users AS u ON u.id = p.user_id "
            "JOIN user_follows AS mine ON mine.follower_id = %(me)s AND mine.followed_id = p.user_id "
            "JOIN user_follows AS theirs ON theirs.follower_id = p.user_id AND theirs.followed_id = %(me)s "
            "WHERE p.event_id = %(event_id)s ORDER BY lower(u.username), u.id",
            {"me": user_id, "event_id": event_id},
        )
        return cursor.fetchall()


def mutual_friend(user_id: int, friend_id: int) -> dict | None:
    """The friend's public profile if the two accounts follow each other, else None."""
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT u.id, u.username, u.display_name FROM users AS u "
            "JOIN user_follows AS mine ON mine.follower_id = %(me)s AND mine.followed_id = u.id "
            "JOIN user_follows AS theirs ON theirs.follower_id = u.id AND theirs.followed_id = %(me)s "
            "WHERE u.id = %(friend)s",
            {"me": user_id, "friend": friend_id},
        )
        return cursor.fetchone()

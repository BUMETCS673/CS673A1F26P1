"""Account and session storage. Routes call these helpers instead of writing SQL."""

import hashlib
import secrets
from datetime import timedelta

import psycopg

from app.database import get_connection

SESSION_LIFETIME = timedelta(days=7)
USER_COLUMNS = "id, username, email, display_name, activity_preferences"


class DuplicateAccountError(Exception):
    """The username or email already belongs to an account."""

    def __init__(self, field: str):
        super().__init__(field)
        self.field = field


def _user(row: tuple) -> dict:
    user_id, username, email, display_name, preferences = row
    return {"id": user_id, "username": username, "email": email,
            "display_name": display_name, "activity_preferences": list(preferences)}


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(username: str, email: str, display_name: str, password_hash: str,
                activity_preferences: list[str]) -> dict:
    """Insert a user; names and emails are unique regardless of letter case."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT lower(username) = lower(%s), lower(email) = lower(%s) FROM users "
                "WHERE lower(username) = lower(%s) OR lower(email) = lower(%s)",
                (username, email, username, email),
            )
            existing = cursor.fetchone()
            if existing:
                raise DuplicateAccountError("username" if existing[0] else "email")
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, display_name, password_hash, "
                    f"activity_preferences) VALUES (%s, %s, %s, %s, %s) RETURNING {USER_COLUMNS}",
                    (username, email, display_name, password_hash, activity_preferences),
                )
            except psycopg.errors.UniqueViolation as error:
                # Two simultaneous registrations can both pass the check above.
                constraint = error.diag.constraint_name or ""
                raise DuplicateAccountError("email" if "email" in constraint else "username") from None
            return _user(cursor.fetchone())


def find_login(username: str) -> tuple[dict, str | None] | None:
    """Return (user, password_hash) for a case-insensitive username, or None."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {USER_COLUMNS}, password_hash FROM users "
                "WHERE lower(username) = lower(%s) ORDER BY id LIMIT 1",
                (username,),
            )
            row = cursor.fetchone()
    return (_user(row[:5]), row[5]) if row else None


def create_session(user_id: int) -> str:
    """Store a new session and return the browser token (only its hash is saved)."""
    token = secrets.token_urlsafe(32)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            # Tidy this user's expired sessions so the table does not keep growing.
            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s AND expires_at <= now()",
                           (user_id,))
            cursor.execute(
                "INSERT INTO user_sessions (token_hash, user_id, expires_at) "
                "VALUES (%s, %s, now() + %s)",
                (_token_hash(token), user_id, SESSION_LIFETIME),
            )
    return token


def get_session_user(token: str) -> dict | None:
    """Return the logged-in user for an unexpired session token, or None."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {USER_COLUMNS} FROM users WHERE id = ("
                "SELECT user_id FROM user_sessions WHERE token_hash = %s AND expires_at > now())",
                (_token_hash(token),),
            )
            row = cursor.fetchone()
    return _user(row) if row else None


def delete_session(token: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM user_sessions WHERE token_hash = %s", (_token_hash(token),))

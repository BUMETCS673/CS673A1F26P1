# AI-USAGE SUMMARY
# Authors: Yuchen Xu (feature requirements)
# Tools: OpenAI Codex
# Overall AI Contribution: Codex drafted this module.
# AI-Assisted Areas: Parameterized PostgreSQL queries for search and follows.
# Human Contributions: Yuchen Xu confirmed the one-way follow model.
# Notes/Verification: tests/live_follows.py exercises these queries through the API.

"""Database operations for directed follows and public user profiles."""

from psycopg.rows import dict_row

from app.database import get_connection


def search_users(username: str, current_user_id: int) -> list[dict]:
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT id, username, display_name FROM users "
            "WHERE lower(username) = lower(%s) AND id <> %s ORDER BY id",
            (username, current_user_id),
        )
        return cursor.fetchall()


def list_following(user_id: int) -> list[dict]:
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT u.id, u.username, u.display_name FROM user_follows AS f "
            "JOIN users AS u ON u.id = f.followed_id WHERE f.follower_id = %s "
            "ORDER BY lower(u.username), u.id",
            (user_id,),
        )
        return cursor.fetchall()


def list_followers(user_id: int) -> list[dict]:
    with get_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT u.id, u.username, u.display_name FROM user_follows AS f "
            "JOIN users AS u ON u.id = f.follower_id WHERE f.followed_id = %s "
            "ORDER BY lower(u.username), u.id",
            (user_id,),
        )
        return cursor.fetchall()


def add_follow(follower_id: int, followed_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO user_follows (follower_id, followed_id) VALUES (%s, %s) "
            "ON CONFLICT (follower_id, followed_id) DO NOTHING",
            (follower_id, followed_id),
        )


def remove_follow(follower_id: int, followed_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM user_follows WHERE follower_id = %s AND followed_id = %s",
            (follower_id, followed_id),
        )

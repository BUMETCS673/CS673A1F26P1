"""One connection per operation; configuration and credentials stay on the server."""

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg


class DatabaseConfigurationError(ValueError):
    """Safe error for missing or invalid server configuration."""


def connection_options() -> dict:
    """Read configuration when connecting, without connecting during import."""
    required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    if any(not os.environ.get(name, "").strip() for name in required):
        raise DatabaseConfigurationError("Database configuration is unavailable.")

    # A single host keeps connect_timeout from multiplying across a host list.
    if "," in os.environ["DB_HOST"]:
        raise DatabaseConfigurationError("Database configuration is unavailable.")
    try:
        port = int(os.environ.get("DB_PORT", "5432"))
        connect_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", "3"))
        statement_timeout = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS", "2000"))
        if not (1 <= port <= 65535 and 2 <= connect_timeout <= 5
                and 1 <= statement_timeout <= 5000):
            raise ValueError
    except ValueError:
        raise DatabaseConfigurationError("Database configuration is unavailable.") from None

    return {
        "host": os.environ["DB_HOST"],
        "port": port,
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "connect_timeout": connect_timeout,
        "options": f"-c statement_timeout={statement_timeout}",
    }


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Commit on success, roll back on error, and close in either case."""
    with psycopg.connect(**connection_options()) as connection:
        yield connection

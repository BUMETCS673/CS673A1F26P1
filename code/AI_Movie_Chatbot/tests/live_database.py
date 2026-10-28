# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: live PostgreSQL checks
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: run against the Docker database

"""Explicit live checks: python -m unittest discover -s tests -p live_database.py -v."""

import os
import socket
import threading
import time
import unittest
from unittest.mock import patch

import psycopg

from app.database import get_connection


class LiveDatabaseTests(unittest.TestCase):
    def test_successful_connection_is_closed(self):
        with get_connection() as connection:
            self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))
        self.assertTrue(connection.closed)

    def test_query_error_closes_connection(self):
        with self.assertRaises(psycopg.errors.DivisionByZero):
            with get_connection() as connection:
                connection.execute("SELECT 1 / 0")
        self.assertTrue(connection.closed)

    def test_slow_query_times_out_and_closes_connection(self):
        started = time.monotonic()
        with patch.dict(os.environ, {"DB_STATEMENT_TIMEOUT_MS": "250"}):
            with self.assertRaises(psycopg.errors.QueryCanceled):
                with get_connection() as connection:
                    connection.execute("SELECT pg_sleep(3)")
        self.assertTrue(connection.closed)
        self.assertLess(time.monotonic() - started, 2)

    def test_unresponsive_server_hits_connection_timeout(self):
        release = threading.Event()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            listener.settimeout(5)

            def accept_without_answering():
                with listener.accept()[0]:
                    release.wait(5)

            worker = threading.Thread(target=accept_without_answering, daemon=True)
            worker.start()
            started = time.monotonic()
            try:
                with patch.dict(os.environ, {
                    "DB_HOST": "127.0.0.1",
                    "DB_PORT": str(listener.getsockname()[1]),
                    "DB_CONNECT_TIMEOUT": "2",
                }):
                    with self.assertRaises(psycopg.OperationalError):
                        with get_connection():
                            self.fail("The fake database must not connect successfully")
                elapsed = time.monotonic() - started
                self.assertGreaterEqual(elapsed, 1.5)
                self.assertLess(elapsed, 4)
            finally:
                release.set()
                worker.join(timeout=5)


if __name__ == "__main__":
    unittest.main()

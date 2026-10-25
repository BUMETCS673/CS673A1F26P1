"""Database configuration and HTTP failure contracts; no live database required."""

import os
import unittest
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

from app.database import DatabaseConfigurationError, connection_options
from app.main import create_app

CONFIG = {
    "DB_HOST": "database",
    "DB_NAME": "example_database",
    "DB_USER": "example_user",
    "DB_PASSWORD": "do-not-leak-this-password",
}


@patch.dict(os.environ, CONFIG, clear=True)
class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_connection_settings_come_from_environment(self):
        with patch.dict(os.environ, {
            "DB_PORT": "5433", "DB_CONNECT_TIMEOUT": "4",
            "DB_STATEMENT_TIMEOUT_MS": "1500",
        }):
            self.assertEqual(connection_options(), {
                "host": "database", "port": 5433, "dbname": "example_database",
                "user": "example_user", "password": CONFIG["DB_PASSWORD"],
                "connect_timeout": 4, "options": "-c statement_timeout=1500",
            })

    def test_missing_required_configuration_is_rejected_safely(self):
        for key in CONFIG:
            with self.subTest(key=key), patch.dict(os.environ, {key: ""}):
                with self.assertRaises(DatabaseConfigurationError) as error:
                    connection_options()
                self.assertNotIn(CONFIG["DB_PASSWORD"], str(error.exception))

    def test_invalid_numbers_and_multiple_hosts_are_rejected(self):
        for key, value in (
            ("DB_PORT", "0"), ("DB_PORT", "65536"), ("DB_PORT", "bad-value"),
            ("DB_CONNECT_TIMEOUT", "0"), ("DB_CONNECT_TIMEOUT", "6"),
            ("DB_STATEMENT_TIMEOUT_MS", "0"), ("DB_STATEMENT_TIMEOUT_MS", "5001"),
            ("DB_HOST", "first,second"),
        ):
            with self.subTest(key=key, value=value), patch.dict(os.environ, {key: value}):
                with self.assertRaises(DatabaseConfigurationError):
                    connection_options()

    @patch("app.database.psycopg.connect")
    def test_diagnostic_executes_select_one_without_user_data(self, connect):
        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1,)
        response = self.client.get("/api/health/database")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})
        cursor.execute.assert_called_once_with("SELECT 1")

    @patch("app.database.psycopg.connect")
    def test_driver_failure_is_a_safe_503(self, connect):
        connect.side_effect = psycopg.OperationalError(
            f"host=private-host password={CONFIG['DB_PASSWORD']} connection refused"
        )
        response = self.client.get("/api/health/database")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {
            "detail": "Database unavailable. Check the backend configuration and database service."
        })
        self.assertNotIn(CONFIG["DB_PASSWORD"], response.text)
        self.assertNotIn("private-host", response.text)

    @patch("app.database.psycopg.connect")
    def test_query_failure_is_a_safe_503(self, connect):
        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = psycopg.errors.QueryCanceled("private query details")
        response = self.client.get("/api/health/database")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private query details", response.text)

    @patch("app.database.psycopg.connect")
    def test_unexpected_result_does_not_report_healthy(self, connect):
        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (0,)
        self.assertEqual(self.client.get("/api/health/database").status_code, 503)

    @patch("app.database.psycopg.connect")
    def test_missing_configuration_fails_without_opening_a_connection(self, connect):
        with patch.dict(os.environ, {"DB_PASSWORD": ""}):
            response = self.client.get("/api/health/database")
        self.assertEqual(response.status_code, 503)
        connect.assert_not_called()

    @patch("app.database.psycopg.connect")
    def test_liveness_does_not_depend_on_the_database(self, connect):
        connect.side_effect = psycopg.OperationalError("database offline")
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        connect.assert_not_called()

    def test_openapi_documents_the_diagnostic_and_503(self):
        schema = self.client.get("/openapi.json").json()
        diagnostic = schema["paths"]["/api/health/database"]["get"]
        self.assertIn("503", diagnostic["responses"])


if __name__ == "__main__":
    unittest.main()

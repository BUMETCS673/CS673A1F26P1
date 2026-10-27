"""Explicit live checks: python -m unittest discover -s tests -p live_auth.py -v.

Needs the running PostgreSQL database and the DB_* variables from README.md.
Every account created here is deleted again, along with its sessions.
"""

import secrets
import unittest

from fastapi.testclient import TestClient

from app import users
from app.database import get_connection
from app.main import create_app


class LiveAuthTests(unittest.TestCase):
    def setUp(self):
        self.username = f"live_test_{secrets.token_hex(4)}"
        self.addCleanup(self.delete_test_user)
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def delete_test_user(self):
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE username = %s", (self.username,))

    def account(self, **changes):
        return {"username": self.username, "display_name": "Live Test",
                "email": f"{self.username}@Example.com", "password": "live password",
                "activity_preferences": ["Food", "Social"], **changes}

    def test_register_login_me_logout_round_trip(self):
        registered = self.client.post("/api/auth/register", json=self.account())
        self.assertEqual(registered.status_code, 201, registered.text)

        with get_connection() as connection:
            row = connection.execute(
                "SELECT email, display_name, password_hash, activity_preferences "
                "FROM users WHERE username = %s", (self.username,)).fetchone()
        self.assertEqual(row[0], f"{self.username}@example.com")
        self.assertEqual(row[1], "Live Test")
        self.assertTrue(row[2].startswith("scrypt$"))
        self.assertEqual(row[3], ["Food", "Social"])

        duplicate = self.client.post("/api/auth/register",
                                     json=self.account(username=self.username.upper()))
        self.assertEqual(duplicate.status_code, 409)

        wrong = self.client.post("/api/auth/login",
                                 json={"username": self.username, "password": "nope nope"})
        self.assertEqual(wrong.status_code, 401)

        login = self.client.post("/api/auth/login",
                                 json={"username": self.username, "password": "live password"})
        self.assertEqual(login.status_code, 200, login.text)
        token = self.client.cookies.get("session")
        with get_connection() as connection:
            stored = connection.execute(
                "SELECT token_hash, expires_at > now() + interval '6 days' FROM user_sessions "
                "WHERE user_id = %s", (registered.json()["id"],)).fetchall()
        self.assertEqual(len(stored), 1)
        self.assertNotEqual(stored[0][0], token, "only a hash of the token is stored")
        self.assertTrue(stored[0][1])

        self.assertEqual(self.client.get("/api/auth/me").json()["username"], self.username)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.client.cookies.set("session", token)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_expired_session_is_rejected(self):
        user = self.client.post("/api/auth/register", json=self.account()).json()
        token = users.create_session(user["id"])
        self.assertEqual(users.get_session_user(token)["id"], user["id"])
        with get_connection() as connection:
            connection.execute("UPDATE user_sessions SET expires_at = now() - interval '1 second' "
                               "WHERE user_id = %s", (user["id"],))
        self.assertIsNone(users.get_session_user(token))

    def test_sample_users_without_passwords_cannot_log_in(self):
        response = self.client.post("/api/auth/login",
                                    json={"username": "sample_alex", "password": "anything"})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()

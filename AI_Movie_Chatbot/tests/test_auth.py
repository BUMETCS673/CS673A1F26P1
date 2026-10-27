"""Auth API contracts with an in-memory account store; no database required.

The SQL in app/users.py is exercised against PostgreSQL by live_auth.py.
"""

import unittest
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

from app import users
from app.main import create_app
from app.passwords import hash_password, verify_password

NEW_USER = {
    "username": "river_fan", "display_name": "River Fan", "email": "River@Example.com",
    "password": "correct horse", "activity_preferences": ["Music", "Outdoors"],
}


class FakeAccounts:
    """Mimics app.users closely enough to test the routes' behavior."""

    def __init__(self):
        self.accounts, self.sessions = [], {}

    def create_user(self, username, email, display_name, password_hash, activity_preferences):
        for account in self.accounts:
            if account["username"].lower() == username.lower():
                raise users.DuplicateAccountError("username")
            if account["email"].lower() == email.lower():
                raise users.DuplicateAccountError("email")
        user = {"id": len(self.accounts) + 1, "username": username, "email": email,
                "display_name": display_name, "activity_preferences": activity_preferences}
        self.accounts.append({**user, "password_hash": password_hash})
        return user

    def find_login(self, username):
        for account in self.accounts:
            if account["username"].lower() == username.lower():
                user = {key: value for key, value in account.items() if key != "password_hash"}
                return user, account["password_hash"]
        return None

    def create_session(self, user_id):
        token = f"token-{len(self.sessions) + 1}"
        self.sessions[token] = user_id
        return token

    def get_session_user(self, token):
        user_id = self.sessions.get(token)
        return self.find_login(self.accounts[user_id - 1]["username"])[0] if user_id else None

    def delete_session(self, token):
        self.sessions.pop(token, None)


class AuthApiTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeAccounts()
        for name in ("create_user", "find_login", "create_session",
                     "get_session_user", "delete_session"):
            patcher = patch.object(users, name, getattr(self.store, name))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def register(self, **changes):
        return self.client.post("/api/auth/register", json={**NEW_USER, **changes})

    def login(self, username="river_fan", password="correct horse"):
        return self.client.post("/api/auth/login", json={"username": username, "password": password})

    def test_register_stores_hashed_password_and_normalized_email(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {
            "id": 1, "username": "river_fan", "display_name": "River Fan",
            "email": "river@example.com", "activity_preferences": ["Music", "Outdoors"],
        })
        stored = self.store.accounts[0]["password_hash"]
        self.assertNotIn("correct horse", stored)
        self.assertTrue(verify_password("correct horse", stored))
        self.assertNotIn("set-cookie", response.headers)

    def test_duplicate_username_or_email_is_409_ignoring_case(self):
        self.register()
        cases = (({"username": "RIVER_FAN", "email": "new@example.com"}, "username"),
                 ({"username": "someone_else", "email": "river@EXAMPLE.com"}, "email"))
        for changes, field in cases:
            with self.subTest(field=field):
                response = self.register(**changes)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json(), {"detail": f"That {field} is already registered."})

    def test_register_rejects_invalid_fields(self):
        cases = {
            "username": "ab", "display_name": "   ", "email": "not-an-email",
            "password": "short", "activity_preferences": [],
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                self.assertEqual(self.register(**{field: value}).status_code, 422)
        with self.subTest(field="unknown preference"):
            self.assertEqual(self.register(activity_preferences=["Sports"]).status_code, 422)
        self.assertEqual(self.store.accounts, [])

    def test_login_sets_http_only_cookie_and_me_returns_user(self):
        self.register()
        response = self.login(username="River_Fan")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "river_fan")
        cookie = response.headers["set-cookie"]
        for attribute in ("session=token-1", "HttpOnly", "Path=/api", "SameSite=lax", "Max-Age=604800"):
            self.assertIn(attribute, cookie)
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["display_name"], "River Fan")

    def test_wrong_password_and_unknown_user_get_the_same_401(self):
        self.register()
        for username, password in (("river_fan", "wrong password"), ("nobody", "correct horse")):
            with self.subTest(username=username):
                response = self.login(username, password)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"detail": "Incorrect username or password."})
                self.assertNotIn("set-cookie", response.headers)
        self.assertEqual(self.store.sessions, {})

    def test_account_without_password_cannot_log_in(self):
        # The two sample database users have no password_hash.
        self.store.accounts.append({"id": 1, "username": "sample_alex", "email": "alex@example.com",
                                    "display_name": None, "activity_preferences": [],
                                    "password_hash": None})
        self.assertEqual(self.login("sample_alex", "anything").status_code, 401)

    def test_me_without_or_with_unknown_session_is_401(self):
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.client.cookies.set("session", "made-up-token")
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not logged in."})

    def test_logout_deletes_session_and_clears_cookie(self):
        self.register()
        self.login()
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertIn('session=""', response.headers["set-cookie"])
        self.assertEqual(self.store.sessions, {})
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_old_session_token_is_rejected_after_logout(self):
        self.register()
        self.login()
        token = self.client.cookies.get("session")
        self.client.post("/api/auth/logout")
        self.client.cookies.set("session", token)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_logout_without_session_still_succeeds(self):
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)

    def test_database_failure_is_a_safe_503(self):
        failure = psycopg.OperationalError("password=secret host=private-host")
        self.client.cookies.set("session", "x")
        requests = (
            ("create_user", lambda: self.register()),
            ("find_login", lambda: self.login()),
            ("get_session_user", lambda: self.client.get("/api/auth/me")),
        )
        for name, send in requests:
            with self.subTest(helper=name), patch.object(users, name, side_effect=failure):
                response = send()
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("secret", response.text)
                self.assertNotIn("private-host", response.text)

    def test_logout_clears_cookie_even_if_database_fails(self):
        self.client.cookies.set("session", "x")
        with patch.object(users, "delete_session", side_effect=psycopg.OperationalError("down")):
            response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 204)
        self.assertIn('session=""', response.headers["set-cookie"])


class PasswordTests(unittest.TestCase):
    def test_hash_is_salted_and_verifies(self):
        first, second = hash_password("same password"), hash_password("same password")
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("scrypt$"))
        self.assertTrue(verify_password("same password", first))
        self.assertFalse(verify_password("other password", first))

    def test_missing_or_malformed_hash_never_matches(self):
        for stored in (None, "", "plain-text", "md5$a$b$c$d$e", "scrypt$x$8$1$AA==$AA=="):
            with self.subTest(stored=stored):
                self.assertFalse(verify_password("anything", stored))


if __name__ == "__main__":
    unittest.main()

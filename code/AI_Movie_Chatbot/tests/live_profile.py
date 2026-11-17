# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over FV-103 from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: two-account profile update checks against PostgreSQL (FV-103)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: run against a PostgreSQL database with all migrations applied (also run by the PR checks)

"""Profile updates with real sessions and PostgreSQL, using two accounts.

Run from AI_Movie_Chatbot with the database variables set (see README):
python -m unittest discover -s tests -p live_profile.py -v
"""

import secrets
import unittest

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import create_app


class LiveProfileTests(unittest.TestCase):
    def account(self, name):
        client = TestClient(create_app())
        self.addCleanup(client.close)
        username = f"{name}_{secrets.token_hex(4)}"
        credentials = {"username": username, "password": "live test password"}
        response = client.post("/api/auth/register", json=credentials | {
            "display_name": name.title(), "email": f"{username}@example.com", "activity_preferences": ["Music"],
        })
        self.assertEqual(response.status_code, 201, response.text)
        user_id = response.json()["id"]
        self.addCleanup(self.delete_account, user_id)
        self.assertEqual(client.post("/api/auth/login", json=credentials).status_code, 200)
        return client, user_id, credentials

    def delete_account(self, user_id):
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = %s", (user_id,))

    def stored(self, user_id):
        with get_connection() as connection:
            return connection.execute(
                "SELECT username, email, display_name, activity_preferences, password_hash IS NOT NULL "
                "FROM users WHERE id = %s", (user_id,)).fetchone()

    def test_update_persists_and_only_changes_the_session_account(self):
        alex, alex_id, credentials = self.account("alex")
        sam, sam_id, _ = self.account("sam")
        before_sam = self.stored(sam_id)
        username, email = self.stored(alex_id)[:2]

        response = alex.patch("/api/auth/me", json={"display_name": "Alex P.",
                                                    "activity_preferences": ["Arts", "Food", "Arts"]})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["activity_preferences"], ["Arts", "Food"])
        self.assertEqual(self.stored(alex_id), (username, email, "Alex P.", ["Arts", "Food"], True))
        self.assertEqual(self.stored(sam_id), before_sam)

        # Only one field: the other is kept.
        alex.patch("/api/auth/me", json={"activity_preferences": ["Social"]})
        self.assertEqual(self.stored(alex_id)[2:4], ("Alex P.", ["Social"]))

        # Survives signing out and back in; the password still works.
        self.assertEqual(alex.post("/api/auth/logout").status_code, 204)
        self.assertEqual(alex.patch("/api/auth/me", json={"display_name": "X"}).status_code, 401)
        self.assertEqual(alex.post("/api/auth/login", json=credentials).status_code, 200)
        me = alex.get("/api/auth/me").json()
        self.assertEqual((me["display_name"], me["activity_preferences"]), ("Alex P.", ["Social"]))

        # Invalid updates change nothing.
        for body in ({"display_name": " "}, {"activity_preferences": []}, {"email": "new@example.com"}, {}):
            with self.subTest(body=body):
                self.assertEqual(alex.patch("/api/auth/me", json=body).status_code, 422)
        self.assertEqual(self.stored(alex_id), (username, email, "Alex P.", ["Social"], True))

    def test_requires_login(self):
        with TestClient(create_app()) as guest:
            self.assertEqual(guest.patch("/api/auth/me", json={"display_name": "X"}).status_code, 401)

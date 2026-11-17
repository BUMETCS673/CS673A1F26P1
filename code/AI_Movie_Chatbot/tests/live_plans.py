# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: two-account My Plans checks against PostgreSQL (FV-95)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: run against a PostgreSQL database with all migrations applied (also run by the PR checks)

"""My Plans with real sessions and PostgreSQL storage, using two accounts.

Run from AI_Movie_Chatbot with the database variables set (see README):
python -m unittest discover -s tests -p live_plans.py -v
"""

import secrets
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import create_app
from app.routes import events as events_route

# Before every demo event, so all of them are upcoming whatever today's date is.
BEFORE_THE_CATALOG = datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("America/New_York"))


class LivePlansTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(events_route, "current_time", lambda: self.now)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.now = BEFORE_THE_CATALOG
        catalog = events_route.load_sample_events()
        first, second = sorted(catalog, key=lambda event: (event["start"], event["id"]))[:2]
        self.early, self.later = first["id"], second["id"]

    def signed_in_account(self):
        client = TestClient(create_app())
        self.addCleanup(client.close)
        username = f"plans_test_{secrets.token_hex(4)}"
        password = "live test password"
        response = client.post("/api/auth/register", json={
            "username": username,
            "display_name": username.title(),
            "email": f"{username}@example.com",
            "password": password,
            "activity_preferences": ["Music"],
        })
        self.assertEqual(response.status_code, 201, response.text)
        user_id = response.json()["id"]
        self.addCleanup(self.delete_account, user_id)
        credentials = {"username": username, "password": password}
        self.assertEqual(client.post("/api/auth/login", json=credentials).status_code, 200)
        return client, user_id, credentials

    def delete_account(self, user_id):
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = %s", (user_id,))

    def saved_ids(self, client):
        response = client.get("/api/plans")
        self.assertEqual(response.status_code, 200, response.text)
        return [plan["event"]["id"] for plan in response.json()["plans"]]

    def stored_rows(self, user_id):
        with get_connection() as connection:
            return connection.execute(
                "SELECT event_id FROM user_plans WHERE user_id = %s ORDER BY event_id", (user_id,)
            ).fetchall()

    def test_plans_require_login(self):
        with TestClient(create_app()) as guest:
            for method in ("GET", "PUT", "DELETE"):
                path = "/api/plans" if method == "GET" else f"/api/plans/{self.early}"
                with self.subTest(method=method):
                    self.assertEqual(guest.request(method, path).status_code, 401)

    def test_plans_persist_across_sign_out_and_are_private_per_account(self):
        alice, alice_id, alice_credentials = self.signed_in_account()
        bob, bob_id, _ = self.signed_in_account()

        # Save in reverse start order, and twice: the list is by start time, no duplicates.
        for event_id in (self.later, self.early, self.later):
            self.assertEqual(alice.put(f"/api/plans/{event_id}").status_code, 204)
        self.assertEqual(self.saved_ids(alice), [self.early, self.later])
        self.assertEqual(len(self.stored_rows(alice_id)), 2)
        self.assertEqual(alice.put("/api/plans/no-such-event").status_code, 404)

        # Bob sees nothing of Alice's and cannot remove her plans.
        self.assertEqual(self.saved_ids(bob), [])
        self.assertEqual(bob.delete(f"/api/plans/{self.early}", params={"user_id": alice_id}).status_code, 204)
        self.assertEqual(bob.put(f"/api/plans/{self.later}").status_code, 204)
        self.assertEqual(self.saved_ids(bob), [self.later])

        # Signing out and back in keeps Alice's plans.
        self.assertEqual(alice.post("/api/auth/logout").status_code, 204)
        self.assertEqual(alice.get("/api/plans").status_code, 401)
        self.assertEqual(alice.put(f"/api/plans/{self.early}").status_code, 401)
        self.assertEqual(alice.post("/api/auth/login", json=alice_credentials).status_code, 200)
        self.assertEqual(self.saved_ids(alice), [self.early, self.later])

        # Removing is idempotent and only affects the signed-in account.
        for _ in range(2):
            self.assertEqual(alice.delete(f"/api/plans/{self.later}").status_code, 204)
        self.assertEqual(self.saved_ids(alice), [self.early])
        self.assertEqual(self.saved_ids(bob), [self.later])

        # Deleting an account deletes its plans (ON DELETE CASCADE).
        self.delete_account(bob_id)
        self.assertEqual(self.stored_rows(bob_id), [])

    def test_ended_plans_stay_listed_and_cannot_be_saved_again(self):
        alice, _, _ = self.signed_in_account()
        self.assertEqual(alice.put(f"/api/plans/{self.early}").status_code, 204)
        self.now = datetime(2027, 6, 1, tzinfo=ZoneInfo("America/New_York"))  # every demo event ended
        response = alice.get("/api/plans")
        self.assertEqual([(plan["event"]["id"], plan["ended"]) for plan in response.json()["plans"]],
                         [(self.early, True)])
        self.assertEqual(alice.put(f"/api/plans/{self.later}").status_code, 409)
        self.assertEqual(alice.delete(f"/api/plans/{self.early}").status_code, 204)
        self.assertEqual(self.saved_ids(alice), [])

    def test_saved_at_is_a_real_timestamp_with_time_zone(self):
        alice, _, _ = self.signed_in_account()
        before = datetime.now(ZoneInfo("UTC"))
        alice.put(f"/api/plans/{self.early}")
        (plan,) = alice.get("/api/plans").json()["plans"]
        saved_at = datetime.fromisoformat(plan["saved_at"])
        self.assertIsNotNone(saved_at.tzinfo)
        self.assertLess(abs((saved_at - before).total_seconds()), 60)

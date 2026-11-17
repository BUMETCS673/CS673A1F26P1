# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over FV-103 from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: PATCH /api/auth/me tests with an in-memory account store (FV-103)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: all tests pass without a database; tests/live_profile.py covers PostgreSQL

"""Profile update API tests. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v."""

import unittest
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

from app import users
from app.main import create_app
from tests.test_auth import FakeAccounts

ALEX = {"username": "alex", "display_name": "Alex", "email": "alex@example.com",
        "password": "alex password", "activity_preferences": ["Music"]}
SAM = {"username": "sam", "display_name": "Sam", "email": "sam@example.com",
       "password": "sam password", "activity_preferences": ["Food"]}


class FakeProfiles(FakeAccounts):
    def update_profile(self, user_id, display_name=None, activity_preferences=None):
        account = self.accounts[user_id - 1]
        if display_name is not None:
            account["display_name"] = display_name
        if activity_preferences is not None:
            account["activity_preferences"] = activity_preferences
        return {key: value for key, value in account.items() if key != "password_hash"}


class ProfileApiTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeProfiles()
        for name in ("create_user", "find_login", "create_session", "get_session_user",
                     "delete_session", "update_profile"):
            patcher = patch.object(users, name, getattr(self.store, name))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.alex = self.signed_in(ALEX)

    def signed_in(self, account):
        client = TestClient(create_app())
        self.addCleanup(client.close)
        self.assertEqual(client.post("/api/auth/register", json=account).status_code, 201)
        login = {"username": account["username"], "password": account["password"]}
        self.assertEqual(client.post("/api/auth/login", json=login).status_code, 200)
        return client

    def patch_me(self, body, client=None, expected=200):
        response = (client or self.alex).patch("/api/auth/me", json=body)
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def test_requires_login(self):
        with TestClient(create_app()) as guest:
            self.assertEqual(guest.patch("/api/auth/me", json={"display_name": "X"}).status_code, 401)
        self.assertEqual(self.store.accounts[0]["display_name"], "Alex")

    def test_changes_display_name_and_preferences_and_me_reflects_it(self):
        updated = self.patch_me({"display_name": "  Alex P.  ", "activity_preferences": ["Arts", "Food"]})
        self.assertEqual(updated, {"id": 1, "username": "alex", "email": "alex@example.com",
                                   "display_name": "Alex P.", "activity_preferences": ["Arts", "Food"]})
        self.assertEqual(self.alex.get("/api/auth/me").json(), updated)

    def test_a_field_left_out_is_kept(self):
        self.assertEqual(self.patch_me({"display_name": "Lex"})["activity_preferences"], ["Music"])
        self.assertEqual(self.patch_me({"activity_preferences": ["Social"]})["display_name"], "Lex")

    def test_duplicate_preferences_are_removed_keeping_order(self):
        result = self.patch_me({"activity_preferences": ["Food", "Music", "Food"]})
        self.assertEqual(result["activity_preferences"], ["Food", "Music"])

    def test_registration_rules_apply(self):
        cases = {
            "blank display name": {"display_name": "   "},
            "null display name": {"display_name": None},
            "display name too long": {"display_name": "x" * 101},
            "no preferences": {"activity_preferences": []},
            "null preferences": {"activity_preferences": None},
            "unknown preference": {"activity_preferences": ["Sports"]},
            "lowercase preference": {"activity_preferences": ["music"]},
            "too many preferences": {"activity_preferences": ["Music"] * 6},
            "preferences not a list": {"activity_preferences": "Music"},
            "display name not text": {"display_name": 5},
            "nothing to change": {},
        }
        for label, body in cases.items():
            with self.subTest(label):
                self.patch_me(body, expected=422)
        self.assertEqual(self.store.accounts[0]["display_name"], "Alex")
        self.assertEqual(self.store.accounts[0]["activity_preferences"], ["Music"])

    def test_other_fields_cannot_be_changed(self):
        for field, value in (("username", "admin"), ("email", "x@example.com"), ("password", "new password!"),
                             ("id", 2), ("user_id", 2), ("password_hash", "x")):
            with self.subTest(field=field):
                self.patch_me({"display_name": "Alex", field: value}, expected=422)
        account = self.store.accounts[0]
        self.assertEqual((account["username"], account["email"]), ("alex", "alex@example.com"))

    def test_only_the_signed_in_account_changes(self):
        sam = self.signed_in(SAM)
        self.patch_me({"display_name": "Sam 2"}, client=sam)
        self.assertEqual(self.store.accounts[0]["display_name"], "Alex")
        self.assertEqual(self.alex.get("/api/auth/me").json()["display_name"], "Alex")
        # A user ID in the URL query is ignored.
        sam.patch("/api/auth/me", params={"user_id": 1}, json={"display_name": "Hacked"})
        self.assertEqual(self.store.accounts[0]["display_name"], "Alex")

    def test_markup_is_stored_as_plain_text(self):
        name = "<img src=x onerror=alert(1)>"
        self.assertEqual(self.patch_me({"display_name": name})["display_name"], name)

    def test_database_failure_is_503_without_details(self):
        with patch.object(users, "update_profile", side_effect=psycopg.OperationalError("password=secret")):
            response = self.alex.patch("/api/auth/me", json={"display_name": "X"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)

    def test_account_deleted_meanwhile_is_401(self):
        with patch.object(users, "update_profile", return_value=None):
            self.patch_me({"display_name": "X"}, expected=401)

    def test_after_logout_the_old_session_cannot_update(self):
        self.assertEqual(self.alex.post("/api/auth/logout").status_code, 204)
        self.patch_me({"display_name": "X"}, expected=401)


if __name__ == "__main__":
    unittest.main()

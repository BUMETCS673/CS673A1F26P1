# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: two-account chat history checks against PostgreSQL (FV-121)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: run against a PostgreSQL database with all migrations applied (also run by the PR checks)

"""Chat history with real sessions and PostgreSQL storage, using two accounts.

Run from AI_Movie_Chatbot with the database variables set (see README):
python -m unittest discover -s tests -p live_chat_history.py -v
"""

import json
import secrets
import unittest

from fastapi.testclient import TestClient

from app.chat_history import HISTORY_LIMIT, list_recent
from app.database import get_connection
from app.main import create_app


UNCLEAR_REPLY = json.dumps({
    "interpretation": {key: None for key in (
        "category", "date", "time", "time_operator", "location", "location_operator", "timezone",
    )} | {"needs_clarification": True},
    "event_ids": [],
})


class LiveChatHistoryTests(unittest.TestCase):
    def signed_in_account(self):
        client = TestClient(create_app())
        self.addCleanup(client.close)
        username = f"chat_test_{secrets.token_hex(4)}"
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

    def requests(self, client):
        response = client.get("/api/chat/history")
        self.assertEqual(response.status_code, 200, response.text)
        return [message["request_text"] for message in response.json()["messages"]]

    def test_history_requires_login(self):
        with TestClient(create_app()) as guest:
            for method in ("GET", "DELETE"):
                with self.subTest(method=method):
                    self.assertEqual(guest.request(method, "/api/chat/history").status_code, 401)

    def test_history_survives_sign_out_and_is_private_per_account(self):
        alice, alice_id, alice_credentials = self.signed_in_account()
        bob, _, _ = self.signed_in_account()

        for message in ("music", "asdf qwerty", "food near North End"):
            self.assertEqual(alice.post("/api/chat", json={"message": message}).status_code, 200)
        self.assertEqual(bob.post("/api/chat", json={"message": "arts"}).status_code, 200)

        # Signing out and back in keeps Alice's history, in order.
        self.assertEqual(alice.post("/api/auth/logout").status_code, 204)
        self.assertEqual(alice.get("/api/chat/history").status_code, 401)
        self.assertEqual(alice.post("/api/auth/login", json=alice_credentials).status_code, 200)
        self.assertEqual(self.requests(alice), ["music", "asdf qwerty", "food near North End"])
        self.assertEqual(self.requests(bob), ["arts"])

        # Bob cannot read or clear Alice's history by naming her account.
        self.assertEqual(self.requests(bob), ["arts"])
        bob.request("DELETE", "/api/chat/history", params={"user_id": alice_id})
        self.assertEqual(bob.get("/api/chat/history", params={"user_id": alice_id}).json()["messages"], [])
        self.assertEqual(len(self.requests(alice)), 3)

        # Alice clearing her history leaves Bob's untouched.
        bob.post("/api/chat", json={"message": "arts"})
        self.assertEqual(alice.delete("/api/chat/history").status_code, 204)
        self.assertEqual(self.requests(alice), [])
        self.assertEqual(self.requests(bob), ["arts"])

    def test_only_the_most_recent_messages_are_loaded(self):
        client, user_id, _ = self.signed_in_account()
        with get_connection() as connection:
            for number in range(HISTORY_LIMIT + 5):
                connection.execute(
                    "INSERT INTO chat_messages (user_id, request_text, reply) VALUES (%s, %s, %s)",
                    (user_id, f"message {number}", UNCLEAR_REPLY),
                )
        rows = list_recent(user_id)
        self.assertEqual(len(rows), HISTORY_LIMIT)
        self.assertEqual(rows[0]["request_text"], "message 5")
        self.assertEqual(rows[-1]["request_text"], f"message {HISTORY_LIMIT + 4}")
        self.assertEqual(len(self.requests(client)), HISTORY_LIMIT)


if __name__ == "__main__":
    unittest.main()

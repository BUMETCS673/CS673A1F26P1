# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: chat history route tests with the storage replaced by a fake (FV-121)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: all tests pass without a database; tests/live_chat_history.py covers PostgreSQL

"""Chat history API tests. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v.

The storage module is replaced by an in-memory fake, so these need no database.
tests/live_chat_history.py runs the same flow against PostgreSQL with two accounts.
"""

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

import psycopg
from fastapi.testclient import TestClient

from app import chat_history
from app.main import create_app
from app.routes import events as events_route
from app.routes.auth import require_user

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))
SAVED_AT = datetime(2026, 11, 14, 20, 0, tzinfo=timezone.utc)


class FakeStorage:
    """Stores rows per user, like the chat_messages table."""

    def __init__(self):
        self.rows = []

    def save_exchange(self, user_id, request_text, interpretation, event_ids):
        self.rows.append({
            "id": len(self.rows) + 1, "user_id": user_id, "request_text": request_text,
            "reply": {"interpretation": interpretation, "event_ids": event_ids},
            "created_at": SAVED_AT,
        })

    def list_recent(self, user_id, limit=chat_history.HISTORY_LIMIT):
        return [row for row in self.rows if row["user_id"] == user_id][-limit:]

    def clear(self, user_id):
        self.rows = [row for row in self.rows if row["user_id"] != user_id]


class ChatHistoryApiTests(unittest.TestCase):
    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            fixture_events = tuple(json.load(fixture_file)["events"])
        self.storage = FakeStorage()
        patches = [
            mock.patch.object(events_route, "load_sample_events", lambda: fixture_events),
            mock.patch.object(events_route, "current_time", lambda: NOW),
        ]
        for name in ("save_exchange", "list_recent", "clear"):
            patches.append(mock.patch.object(chat_history, name, getattr(self.storage, name)))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.application = create_app()
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)
        self.sign_in_as(1)

    def sign_in_as(self, user_id):
        self.application.dependency_overrides[require_user] = lambda: {"id": user_id}

    def history(self):
        response = self.client.get("/api/chat/history")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["messages"]

    def test_each_exchange_is_saved_with_event_ids(self):
        self.client.post("/api/chat", json={"message": "music"})
        (row,) = self.storage.rows
        self.assertEqual(row["user_id"], 1)
        self.assertEqual(row["request_text"], "music")
        self.assertEqual(row["reply"]["event_ids"], ["fixture-06", "fixture-10"])
        self.assertEqual(row["reply"]["interpretation"]["category"], "Music")

    def test_history_rebuilds_cards_from_the_catalog_in_order(self):
        for message in ("music", "asdf qwerty", "music near Mars"):
            self.client.post("/api/chat", json={"message": message})
        messages = self.history()
        self.assertEqual([m["request_text"] for m in messages], ["music", "asdf qwerty", "music near Mars"])
        self.assertEqual([e["id"] for e in messages[0]["events"]], ["fixture-06", "fixture-10"])
        self.assertEqual(messages[0]["events"][0]["title"], "Fixture: Monday open mic")
        self.assertTrue(messages[1]["interpretation"]["needs_clarification"])
        self.assertEqual(messages[2]["events"], [])
        self.assertEqual({m["unavailable_count"] for m in messages}, {0})

    def test_ended_or_removed_events_are_counted_as_unavailable(self):
        self.storage.save_exchange(1, "food", {"category": "Food", "date": None, "time": None,
                                               "time_operator": None, "location": None,
                                               "location_operator": None,
                                               "timezone": "America/New_York",
                                               "needs_clarification": False},
                                   ["fixture-02", "fixture-03", "no-longer-exists"])
        (message,) = self.history()
        self.assertEqual([e["id"] for e in message["events"]], ["fixture-03"])
        self.assertEqual(message["unavailable_count"], 2)

    def test_users_only_see_and_clear_their_own_history(self):
        self.client.post("/api/chat", json={"message": "music"})
        self.sign_in_as(2)
        self.assertEqual(self.history(), [])
        self.client.post("/api/chat", json={"message": "food today"})
        self.assertEqual(self.client.delete("/api/chat/history").status_code, 204)
        self.assertEqual(self.history(), [])
        self.sign_in_as(1)
        self.assertEqual([m["request_text"] for m in self.history()], ["music"])

    def test_failed_save_is_an_error_not_a_reply(self):
        with mock.patch.object(chat_history, "save_exchange", side_effect=psycopg.OperationalError()):
            response = self.client.post("/api/chat", json={"message": "music"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("not saved", response.json()["detail"])
        self.assertNotIn("events", response.json())

    def test_unavailable_database_gives_503(self):
        for name, method in (("list_recent", "GET"), ("clear", "DELETE")):
            with self.subTest(method=method), mock.patch.object(
                chat_history, name, side_effect=psycopg.OperationalError(),
            ):
                self.assertEqual(self.client.request(method, "/api/chat/history").status_code, 503)

    def test_history_requires_login(self):
        self.application.dependency_overrides.clear()
        for method in ("GET", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, "/api/chat/history").status_code, 401)


if __name__ == "__main__":
    unittest.main()

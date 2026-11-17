# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: chat endpoint test cases (FV-125 integration)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the example requests, reviewed every change before committing
# Notes/Verification: all tests pass; independent of today's date

"""Chat API tests. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v.

Requests are answered from tests/fixtures/catalog_events.json at a fixed Boston
time (Sunday 2026-11-15, noon), so results never depend on today's date.
"""

import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app import chat_history
from app.chat import matches_place
from app.main import create_app
from app.routes import events as events_route
from app.routes.auth import require_user

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))


class ChatApiTests(unittest.TestCase):
    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            fixture_events = tuple(json.load(fixture_file)["events"])
        for target, value in (("load_sample_events", lambda: fixture_events), ("current_time", lambda: NOW)):
            patcher = mock.patch.object(events_route, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # Saving history is covered by test_chat_history.py; no database here.
        saver = mock.patch.object(chat_history, "save_exchange")
        saver.start()
        self.addCleanup(saver.stop)
        self.application = create_app()
        self.application.dependency_overrides[require_user] = lambda: {"id": 1}
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)

    def ask(self, message):
        response = self.client.post("/api/chat", json={"message": message})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def ids(self, message):
        return [event["id"] for event in self.ask(message)["events"]]

    def test_category_returns_upcoming_events_in_start_order(self):
        self.assertEqual(self.ids("music"), ["fixture-06", "fixture-10"])

    def test_ended_events_are_not_recommended(self):
        # fixture-02 (Outdoors) ended this morning.
        self.assertEqual(self.ids("outdoors"), ["fixture-08", "fixture-13"])

    def test_weekday_and_today_use_boston_dates(self):
        self.assertEqual(self.ids("arts on wednesday"), ["fixture-07"])
        # fixture-03 is still running at noon; fixture-04 starts at 12:01.
        self.assertEqual(self.ids("events today"), ["fixture-03", "fixture-04"])

    def test_time_constraint_compares_boston_start_times(self):
        self.assertEqual(
            self.ids("events after 7pm"),
            ["fixture-05", "fixture-06", "fixture-10", "fixture-11", "fixture-14"],
        )
        self.assertEqual(self.ids("food before 6pm"), ["fixture-03", "fixture-09"])

    def test_event_crossing_midnight_counts_on_both_days(self):
        self.assertEqual(self.ids("social on 2027-01-01"), ["fixture-11"])
        self.assertEqual(self.ids("social on 2026-12-31"), ["fixture-11"])

    def test_place_matches_location_text_ignoring_case(self):
        self.assertEqual(self.ids("something fun near FENWAY"), ["fixture-05", "fixture-12"])
        self.assertEqual(self.ids("social in fenway"), ["fixture-05"])

    def test_all_constraints_apply_together(self):
        self.assertEqual(self.ids("music tomorrow after 6pm in Allston"), ["fixture-06"])
        self.assertEqual(self.ids("music tomorrow after 8pm in Allston"), [])

    def test_unknown_place_is_an_honest_no_match(self):
        data = self.ask("music near Mars")
        self.assertFalse(data["interpretation"]["needs_clarification"])
        self.assertEqual(data["interpretation"]["location"], "Mars")
        self.assertEqual(data["events"], [])

    def test_unclear_request_asks_for_clarification(self):
        data = self.ask("asdf qwerty")
        self.assertTrue(data["interpretation"]["needs_clarification"])
        self.assertEqual(data["events"], [])

    def test_events_have_catalog_fields(self):
        event = self.ask("food today")["events"][0]
        self.assertEqual(
            set(event), {"id", "title", "category", "start", "end", "location", "description"},
        )

    def test_invalid_bodies_are_rejected(self):
        for body in ({}, {"message": ""}, {"message": 5}, {"message": "music", "extra": 1},
                     {"message": "x" * 1001}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/api/chat", json=body).status_code, 422)

    def test_chat_requires_login(self):
        self.application.dependency_overrides.clear()
        self.assertEqual(self.client.post("/api/chat", json={"message": "music"}).status_code, 401)


class PlaceMatchTests(unittest.TestCase):
    def test_events_without_location_never_match(self):
        self.assertFalse(matches_place({"location": None}, "Fenway"))
        self.assertFalse(matches_place({"location": ""}, "Fenway"))

    def test_extra_spaces_are_ignored(self):
        self.assertTrue(matches_place({"location": "Back  Bay, Boston"}, " back bay "))


if __name__ == "__main__":
    unittest.main()

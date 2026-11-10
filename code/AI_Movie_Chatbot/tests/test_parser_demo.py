# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: OpenAI Codex, prompted by Ji Wu
# Overall AI Contribution: 80%
# AI-Assisted Areas: FV-118 HTTP demo test cases; FV-124 API response fields
# Human Contributions: Ji Wu: requirements, prompts, scope decisions, and review of results
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""FV-118 HTTP demo works independently of event filtering or a catalog."""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.request_parser import parse_event_request


def interpretation(**fields):
    return {
        "category": None, "date": None, "time": None, "time_operator": None,
        "location": None, "location_operator": None, "timezone": "America/New_York",
        "needs_clarification": False, **fields,
    }


class ParserDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_category_only_returns_exact_parser_fields(self):
        response = self.client.post("/api/demo/parse-event-request", json={"message": "mUsIc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), interpretation(category="Music"))

    def test_category_with_date(self):
        response = self.client.post("/api/demo/parse-event-request", json={"message": " Music on 2026-11-01 "})
        self.assertEqual(response.json(), interpretation(category="Music", date="2026-11-01"))

    def test_combined_request_exposes_all_interpreted_constraints(self):
        fixed_instant = datetime(2026, 11, 9, 20, 30, tzinfo=timezone.utc)
        with patch("app.routes.parser_demo.parse_event_request", side_effect=(
            lambda message: parse_event_request(message, now=fixed_instant)
        )):
            response = self.client.post("/api/demo/parse-event-request", json={
                "message": "music in Boston next Friday after 6 pm",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), interpretation(
            category="Music", date="2026-11-20", time="18:00", time_operator="after",
            location="Boston", location_operator="in",
        ))

    def test_invalid_or_unsupported_text_requires_clarification(self):
        for message in ("", "music after 6", "music and food", "music on 2026-02-30", "movies"):
            with self.subTest(message=message):
                response = self.client.post("/api/demo/parse-event-request", json={"message": message})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), interpretation(timezone=None, needs_clarification=True))

    def test_invalid_payloads_are_rejected(self):
        for payload in ({}, {"message": 1}, {"message": "x" * 1001},
                        {"message": "music", "events": []}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/demo/parse-event-request", json=payload).status_code, 422)

    def test_parser_does_not_call_event_filter(self):
        with patch("app.routes.filter_demo.filter_events", side_effect=AssertionError("Unexpected filtering")):
            response = self.client.post("/api/demo/parse-event-request", json={"message": "music"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), interpretation(category="Music"))

    def test_filter_remains_available_alongside_parser(self):
        events = [
            {"id": "concert", "title": "Concert", "category": "Music", "date": "2026-11-01",
             "time": "6 PM", "location": "Boston", "description": "Sample concert"},
            {"id": "art", "title": "Art", "category": "Arts", "date": "2026-11-01",
             "time": "2 PM", "location": "Boston", "description": "Sample art"},
        ]
        with patch("app.routes.parser_demo.parse_event_request", side_effect=AssertionError("Unexpected parsing")):
            response = self.client.post("/api/demo/filter-events", json={
                "events": events, "category": "mUsIc", "date": "2026-11-01",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"], events[:1])


if __name__ == "__main__":
    unittest.main()

# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: OpenAI Codex, prompted by Ji Wu
# Overall AI Contribution: 80%
# AI-Assisted Areas: FV-117 HTTP demo test cases
# Human Contributions: Ji Wu: requirements, prompts, scope decisions, and review of results
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""FV-117 HTTP demo works independently of the request parser."""

import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

from app.main import create_app


class FilterDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)
        self.events = [
            {"id": "a", "title": "Concert", "category": "Music", "date": "2026-11-01",
             "time": "6:00 PM", "location": "Boston", "description": "Sample concert"},
            {"id": "b", "title": "Art", "category": "Arts", "date": "2026-11-01",
             "time": "2:00 PM", "location": "Boston", "description": "Sample art"},
            {"id": "c", "title": "Jazz", "category": "MUSIC", "date": "2026-11-03",
             "time": "3:00 PM", "location": "Boston", "description": "Sample jazz"},
        ]

    def query(self, **filters):
        response = self.client.post("/api/demo/filter-events", json={**filters, "events": self.events})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_no_filters_preserves_all_details_and_order(self):
        before = deepcopy(self.events)
        self.assertEqual(self.query()["events"], self.events)
        self.assertEqual(self.events, before)

    def test_category_case_insensitive(self):
        self.assertEqual(self.query(category="mUsIc")["events"], [self.events[0], self.events[2]])

    def test_date_only(self):
        self.assertEqual(self.query(date="2026-11-01")["events"], self.events[:2])

    def test_combined_filters(self):
        self.assertEqual(self.query(category="music", date="2026-11-01")["events"], self.events[:1])

    def test_no_matches_and_empty_samples(self):
        self.assertEqual(self.query(category="Food")["events"], [])
        self.events = []
        self.assertEqual(self.query()["events"], [])

    def test_invalid_payloads_are_rejected(self):
        for body in ({}, {"events": [{}]}, {"events": self.events, "category": []},
                     {"events": self.events, "message": "music"}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/api/demo/filter-events", json=body).status_code, 422)


if __name__ == "__main__":
    unittest.main()

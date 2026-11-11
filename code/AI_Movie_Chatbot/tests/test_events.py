# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: events endpoint and ordering test cases
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: all tests pass

"""Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v."""

"""API tests for FV-122 and FV-123."""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app


EXPECTED_FIELDS = {
    "id",
    "title",
    "category",
    "start",
    "end",
    "location",
    "description",
}


class EventsApiTests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_events_returns_paginated_response(self):
        response = self.client.get("/api/events?limit=5&offset=0")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertIn("events", data)
        self.assertIn("next_offset", data)
        self.assertEqual(len(data["events"]), 5)
        self.assertEqual(data["next_offset"], 5)

        for event in data["events"]:
            self.assertEqual(set(event), EXPECTED_FIELDS)

    def test_event_details(self):
        response = self.client.get("/api/events/fixture-10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "fixture-10")

    def test_unknown_event_returns_404(self):
        response = self.client.get("/api/events/does-not-exist")

        self.assertEqual(response.status_code, 404)

    def test_invalid_limit_returns_422(self):
        response = self.client.get("/api/events?limit=0")

        self.assertEqual(response.status_code, 422)

    def test_events_rejects_unsupported_method(self):
        response = self.client.post("/api/events")

        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()

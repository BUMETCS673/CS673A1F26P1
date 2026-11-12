# AI-USAGE SUMMARY
# Authors: Daniel Winnie (original tests, merge fixes), Jibek Kelgenbaeva (paginated list and details tests, FV-122/123)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie; Jibek Kelgenbaeva's tools: to be confirmed by the author
# Overall AI Contribution: ~90% (Daniel's parts); Jibek's part to be confirmed by the author
# AI-Assisted Areas: events API test cases with a fixed reference time
# Human Contributions: Jibek Kelgenbaeva: list/details/404/422 test cases; Daniel Winnie: login override, fixed clock, fixture catalog, demo-data checks
# Notes/Verification: all tests pass; independent of today's date

"""Events API tests. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v.

The API is checked against tests/fixtures/catalog_events.json at a fixed Boston
time, so the results never depend on today's date or on the demo data.
"""

import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import create_app
from app.routes import events as events_route
from app.routes.auth import require_user

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))
# Upcoming fixtures at NOW in start order (see test_event_catalog.py).
UPCOMING_IDS = [
    "fixture-03", "fixture-04", "fixture-05", "fixture-06", "fixture-07", "fixture-08",
    "fixture-09", "fixture-10", "fixture-11", "fixture-12", "fixture-14", "fixture-13",
]
EXPECTED_FIELDS = {"id", "title", "category", "start", "end", "location", "description"}


class EventsApiTests(unittest.TestCase):
    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            fixture_events = tuple(json.load(fixture_file)["events"])
        for target, value in (("load_sample_events", lambda: fixture_events), ("current_time", lambda: NOW)):
            patcher = mock.patch.object(events_route, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        application = create_app()
        application.dependency_overrides[require_user] = lambda: {"id": 1}
        self.client = TestClient(application)
        self.addCleanup(self.client.close)

    def page(self, **params):
        response = self.client.get("/api/events", params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_first_page_is_upcoming_events_in_start_order(self):
        data = self.page(limit=5, offset=0)
        self.assertEqual([event["id"] for event in data["events"]], UPCOMING_IDS[:5])
        self.assertEqual(data["next_offset"], 5)
        for event in data["events"]:
            self.assertEqual(set(event), EXPECTED_FIELDS)

    def test_pages_cover_every_upcoming_event_once(self):
        seen, offset = [], 0
        while offset is not None:
            data = self.page(limit=5, offset=offset)
            seen += [event["id"] for event in data["events"]]
            offset = data["next_offset"]
        self.assertEqual(seen, UPCOMING_IDS)

    def test_ended_events_are_hidden(self):
        ids = {event["id"] for event in self.page(limit=50)["events"]}
        self.assertTrue({"fixture-01", "fixture-02"}.isdisjoint(ids))

    def test_offset_past_the_end_returns_an_empty_last_page(self):
        self.assertEqual(self.page(offset=100), {"events": [], "next_offset": None})

    def test_event_details(self):
        response = self.client.get("/api/events/fixture-10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "fixture-10")

    def test_unknown_event_returns_404(self):
        self.assertEqual(self.client.get("/api/events/does-not-exist").status_code, 404)

    def test_invalid_paging_returns_422(self):
        for params in ({"limit": 0}, {"limit": 51}, {"offset": -1}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get("/api/events", params=params).status_code, 422)

    def test_events_rejects_unsupported_method(self):
        self.assertEqual(self.client.post("/api/events").status_code, 405)

    def test_events_require_login(self):
        with TestClient(create_app()) as guest:
            self.assertEqual(guest.get("/api/events").status_code, 401)
            self.assertEqual(guest.get("/api/events/fixture-10").status_code, 401)


class DemoDataTests(unittest.TestCase):
    """The shipped demo file is valid, whatever events it contains."""

    def test_demo_events_are_well_formed(self):
        events_route.load_sample_events.cache_clear()
        events = events_route.load_sample_events()
        self.assertGreater(len(events), 0)
        self.assertEqual(len({event["id"] for event in events}), len(events))
        for event in events:
            with self.subTest(event=event["id"]):
                events_route.CatalogEvent(**event)
                start, end = datetime.fromisoformat(event["start"]), datetime.fromisoformat(event["end"])
                self.assertIsNotNone(start.utcoffset())
                self.assertLess(start, end)
                self.assertNotIn("fixture", event["title"].lower())


if __name__ == "__main__":
    unittest.main()

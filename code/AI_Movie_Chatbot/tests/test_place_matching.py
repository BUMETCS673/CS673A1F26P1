# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over place matching from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: place matching tests with the fixture catalog and a fixed Boston time
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: python -m unittest discover -s tests -v

"""Place matching. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v."""

import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app import chat_history
from app.main import create_app
from app.place_matching import filter_by_place, location_matches, normalize_place
from app.routes import events as events_route
from app.routes.auth import require_user

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"
DEMO = Path(__file__).resolve().parents[1] / "app" / "data" / "sample_events.json"
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))


class LocationMatchTests(unittest.TestCase):
    def test_the_agreed_rule_location_contains_the_place_ignoring_case(self):
        self.assertTrue(location_matches("Fenway, Boston", "Fenway"))
        self.assertTrue(location_matches("Fenway, Boston", "fenway"))
        self.assertTrue(location_matches("North End, Boston", "NORTH END"))
        self.assertTrue(location_matches("Back Bay, Boston", "Boston"))
        self.assertFalse(location_matches("Back Bay, Boston", "Fenway"))

    def test_everyday_wording(self):
        for location, place in (
            ("North End, Boston", "the North End"),
            ("North End, Boston", "north-end"),
            ("North End, Boston", "North End!"),
            ("Back  Bay, Boston", " back   bay "),
            ("Fenway, Boston", "Fenway Park"),         # landmark in the neighborhood
            ("Fenway, Boston", "Fenway, Boston"),
            ("Downtown, Boston", "Downtown Crossing"),
            ("Jamaica Plain, Boston", "jamaica plain"),
            ("South Boston, Boston", "South Boston"),
        ):
            with self.subTest(place=place):
                self.assertTrue(location_matches(location, place))

    def test_whole_words_only(self):
        self.assertFalse(location_matches("Back Bay, Boston", "ston"))
        self.assertFalse(location_matches("Fenway, Boston", "Fen"))
        # "Fenway" must not be found inside an unrelated longer word.
        self.assertFalse(location_matches("Fenway, Boston", "Fenwaystreet"))

    def test_neighborhoods_do_not_match_each_other(self):
        self.assertFalse(location_matches("South End, Boston", "North End"))
        self.assertFalse(location_matches("East Boston, Boston", "South Boston"))
        self.assertFalse(location_matches("South Boston, Boston", "East Boston"))
        self.assertFalse(location_matches("Allston, Boston", "Brighton"))

    def test_missing_location_or_place_never_matches(self):
        for location, place in ((None, "Fenway"), ("", "Fenway"), ("Fenway, Boston", ""),
                                ("Fenway, Boston", None), ("Fenway, Boston", "the"), ("Fenway, Boston", "!!")):
            with self.subTest(location=location, place=place):
                self.assertFalse(location_matches(location, place))

    def test_normalize_place(self):
        self.assertEqual(normalize_place("  The   North-End, Boston! "), "north end boston")
        self.assertEqual(normalize_place("Theater District"), "theater district")  # only a whole leading "the"
        self.assertEqual(normalize_place(None), "")


class FilterByPlaceTests(unittest.TestCase):
    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            self.events = json.load(fixture_file)["events"]

    def ids(self, place):
        return [event["id"] for event in filter_by_place(self.events, place)]

    def test_keeps_matching_events_in_their_order(self):
        self.assertEqual(self.ids("Fenway"), ["fixture-05", "fixture-12"])
        self.assertEqual(self.ids("near the north end".removeprefix("near ")), ["fixture-03"])

    def test_unknown_place_is_an_honest_empty_list(self):
        self.assertEqual(self.ids("Narnia"), [])

    def test_event_without_location_is_never_included(self):
        self.assertNotIn("fixture-09", self.ids("Boston"))
        self.assertEqual(len(self.ids("Boston")), len(self.events) - 1)

    def test_every_demo_neighborhood_can_be_found_by_name(self):
        with DEMO.open(encoding="utf-8") as demo_file:
            demo = json.load(demo_file)["events"]
        for location in {event["location"] for event in demo if event.get("location")}:
            neighborhood = location.split(",")[0]
            with self.subTest(neighborhood=neighborhood):
                found = filter_by_place(demo, neighborhood)
                self.assertTrue(found)
                self.assertTrue(all(event["location"] == location for event in found), neighborhood)


class ChatPlaceTests(unittest.TestCase):
    """The chat uses the shared helper (fixed Boston time, fixture catalog)."""

    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            fixture_events = tuple(json.load(fixture_file)["events"])
        for target, value in (("load_sample_events", lambda: fixture_events), ("current_time", lambda: NOW)):
            patcher = mock.patch.object(events_route, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        saver = mock.patch.object(chat_history, "save_exchange")
        saver.start()
        self.addCleanup(saver.stop)
        application = create_app()
        application.dependency_overrides[require_user] = lambda: {"id": 1, "activity_preferences": []}
        self.client = TestClient(application)
        self.addCleanup(self.client.close)

    def ids(self, message):
        response = self.client.post("/api/chat", json={"message": message})
        self.assertEqual(response.status_code, 200, response.text)
        return [event["id"] for event in response.json()["events"]]

    def test_chat_place_requests(self):
        self.assertEqual(self.ids("food near the North End"), ["fixture-03"])
        self.assertEqual(self.ids("arts near Fenway Park"), ["fixture-12"])
        self.assertEqual(self.ids("social in Fenway"), ["fixture-05"])
        self.assertEqual(self.ids("music near Narnia"), [])

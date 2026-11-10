# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: OpenAI Codex, prompted by Ji Wu
# Overall AI Contribution: 80%
# AI-Assisted Areas: FV-118 parser test cases; FV-124 Boston date, time and location fixtures
# Human Contributions: Ji Wu: requirements, prompts, scope decisions, and review of results
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""Behavioral checks for the Boston event request grammar."""

import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.request_parser import parse_event_request


BOSTON_NOW = datetime(2026, 11, 9, 15, 30, tzinfo=ZoneInfo("America/New_York"))


class EventRequestParserTests(unittest.TestCase):
    def assert_parsed(self, message, **constraints):
        self.assertEqual(parse_event_request(message, now=BOSTON_NOW), {
            "category": None, "date": None, "time": None, "time_operator": None,
            "location": None, "location_operator": None, "timezone": "America/New_York",
            "needs_clarification": False, **constraints,
        })

    def assert_needs_clarification(self, message):
        self.assertEqual(parse_event_request(message, now=BOSTON_NOW), {
            "category": None, "date": None, "time": None, "time_operator": None,
            "location": None, "location_operator": None, "timezone": None,
            "needs_clarification": True,
        })

    def test_each_supported_category_has_canonical_capitalization(self):
        for category in ("Music", "Arts", "Food", "Outdoors", "Social"):
            with self.subTest(category=category):
                self.assert_parsed(category.lower(), category=category)

    def test_mixed_capitalization_and_outer_whitespace(self):
        self.assert_parsed(" \t mUsIc \n", category="Music")

    def test_category_with_valid_iso_date(self):
        self.assert_parsed(" Music on 2026-11-01 ", category="Music", date="2026-11-01")
        self.assert_parsed("2026-11-01", date="2026-11-01")

    def test_dated_request_is_case_insensitive(self):
        self.assert_parsed("fOoD ON 2026-11-02", category="Food", date="2026-11-02")

    def test_valid_leap_day(self):
        self.assert_parsed("arts on 2028-02-29", category="Arts", date="2028-02-29")

    def test_time_constraints_and_clock_boundaries(self):
        for phrase, operator, value in (
            ("after 6 pm", "after", "18:00"),
            ("before 7:15AM", "before", "07:15"),
            ("at 12 am", "at", "00:00"),
            ("at 12 pm", "at", "12:00"),
            ("at 18:30", "at", "18:30"),
        ):
            with self.subTest(phrase=phrase):
                self.assert_parsed(phrase, time=value, time_operator=operator)

    def test_weekdays_and_relative_dates(self):
        for phrase, value in (
            ("Saturday", "2026-11-14"), ("this Monday", "2026-11-09"),
            ("next Friday", "2026-11-20"), ("today", "2026-11-09"), ("tomorrow", "2026-11-10"),
        ):
            with self.subTest(phrase=phrase):
                self.assert_parsed(phrase, date=value)

    def test_reference_instant_converts_to_boston_before_resolving_date(self):
        utc_early_tuesday = datetime(2026, 11, 10, 2, 30, tzinfo=timezone.utc)
        self.assertEqual(parse_event_request("today", now=utc_early_tuesday)["date"], "2026-11-09")
        self.assertEqual(parse_event_request("tomorrow", now=utc_early_tuesday)["date"], "2026-11-10")

    def test_locations(self):
        self.assert_parsed("in Back Bay, Boston", location="Back Bay, Boston", location_operator="in")
        self.assert_parsed("something fun near Fenway", location="Fenway", location_operator="near")

    def test_combined_constraints_in_either_order(self):
        for phrase in ("music in Boston next Friday after 6 pm", "music after 6 pm next Friday in Boston"):
            with self.subTest(phrase=phrase):
                self.assert_parsed(
                    phrase, category="Music", date="2026-11-20", time="18:00",
                    time_operator="after", location="Boston", location_operator="in",
                )

    def test_invalid_dates_require_clarification(self):
        for value in (
            "2026-02-29", "2026-02-30", "2026-13-01", "2026-00-01",
            "2026-11-00", "0000-11-01", "2026-1-01", "20261101",
            "2026-11-01T10:00:00",
        ):
            with self.subTest(date=value):
                self.assert_needs_clarification(f"music on {value}")

    def test_blank_or_unknown_requests_require_clarification(self):
        for message in ("", " \t\n", "movies", "sports", "something fun"):
            with self.subTest(message=message):
                self.assert_needs_clarification(message)

    def test_multiple_categories_require_clarification(self):
        for message in ("music and food", "music food", "music, arts", "music/food"):
            with self.subTest(message=message):
                self.assert_needs_clarification(message)

    def test_unsupported_constraints_are_not_silently_dropped(self):
        for message in (
            "find music", "music on 2026-11-01 tomorrow",
            "musical", "music on", "music on 2026-11-01!", "music near",
            "after 13 pm", "before 00 am", "at 24:00", "at 6:60 pm", "after 6",
            "music at 6 pm before 8 pm", "this tomorrow", "in Boston or Cambridge",
            "in Boston in Cambridge", "music in Boston after sunset",
        ):
            with self.subTest(message=message):
                self.assert_needs_clarification(message)

    def test_results_do_not_share_mutable_state(self):
        result = parse_event_request("unknown")
        result["category"] = "Music"
        self.assert_needs_clarification("unknown")
        self.assertEqual(parse_event_request("music")["category"], "Music")


if __name__ == "__main__":
    unittest.main()

# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: not yet reported by the author - author to confirm in the AIUsageLog
# Overall AI Contribution: to be confirmed by Ji Wu
# AI-Assisted Areas: FV-118 parser test cases
# Human Contributions: Ji Wu: implementation and tests (FV-117 / FV-118)
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""Behavioral checks for FV-118's deliberately small request grammar."""

import unittest

from app.request_parser import parse_event_request


class EventRequestParserTests(unittest.TestCase):
    def assert_needs_clarification(self, message):
        self.assertEqual(
            parse_event_request(message),
            {"category": None, "date": None, "needs_clarification": True},
        )

    def test_each_supported_category_has_canonical_capitalization(self):
        for category in ("Music", "Arts", "Food", "Outdoors", "Social"):
            with self.subTest(category=category):
                self.assertEqual(
                    parse_event_request(category.lower()),
                    {"category": category, "date": None, "needs_clarification": False},
                )

    def test_mixed_capitalization_and_outer_whitespace(self):
        self.assertEqual(
            parse_event_request(" \t mUsIc \n"),
            {"category": "Music", "date": None, "needs_clarification": False},
        )

    def test_category_with_valid_iso_date(self):
        self.assertEqual(
            parse_event_request(" Music on 2026-11-01 "),
            {"category": "Music", "date": "2026-11-01", "needs_clarification": False},
        )

    def test_dated_request_is_case_insensitive(self):
        self.assertEqual(
            parse_event_request("fOoD ON 2026-11-02"),
            {"category": "Food", "date": "2026-11-02", "needs_clarification": False},
        )

    def test_valid_leap_day(self):
        self.assertEqual(
            parse_event_request("arts on 2028-02-29"),
            {"category": "Arts", "date": "2028-02-29", "needs_clarification": False},
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
        for message in ("", " \t\n", "movies", "sports", "2026-11-01"):
            with self.subTest(message=message):
                self.assert_needs_clarification(message)

    def test_multiple_categories_require_clarification(self):
        for message in ("music and food", "music food", "music, arts", "music/food"):
            with self.subTest(message=message):
                self.assert_needs_clarification(message)

    def test_unsupported_constraints_are_not_silently_dropped(self):
        for message in (
            "music tomorrow", "music in Boston", "find music",
            "music on 2026-11-01 at 18:00", "music on 2026-11-01 tomorrow",
            "musical", "music on", "music on 2026-11-01!",
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

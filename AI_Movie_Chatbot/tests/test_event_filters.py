"""Behavioral checks for FV-117, independent of any catalog or endpoint."""

import unittest
from copy import deepcopy

from app.event_filters import filter_events


class EventFilterTests(unittest.TestCase):
    def setUp(self):
        self.events = [
            {"id": "a", "category": "Music", "date": "2026-11-01", "title": "Concert"},
            {"id": "b", "category": "Food", "date": "2026-11-01", "title": "Lunch"},
            {"id": "c", "category": "MUSIC", "date": "2026-11-02", "title": "Jazz"},
            {"id": "d", "category": "Arts", "date": "2026-11-03", "title": "Walk"},
        ]

    def test_no_filters_returns_all_events_in_original_order(self):
        result = filter_events(self.events)
        self.assertEqual(result, self.events)
        self.assertIsNot(result, self.events)

    def test_category_is_case_insensitive_and_preserves_order(self):
        for category in ("music", "Music", "mUsIc", "MUSIC"):
            with self.subTest(category=category):
                self.assertEqual(
                    filter_events(self.events, category=category),
                    [self.events[0], self.events[2]],
                )

    def test_date_only(self):
        self.assertEqual(
            filter_events(self.events, date="2026-11-01"),
            [self.events[0], self.events[1]],
        )

    def test_both_filters_must_match(self):
        self.assertEqual(
            filter_events(self.events, category="music", date="2026-11-02"),
            [self.events[2]],
        )

    def test_no_matches_returns_empty_list(self):
        for filters in (
            {"category": "Social"},
            {"date": "2026-12-01"},
            {"category": "Food", "date": "2026-11-02"},
        ):
            with self.subTest(filters=filters):
                self.assertEqual(filter_events(self.events, **filters), [])

    def test_date_is_an_exact_string_match(self):
        for value in ("2026-11-1", "2026-11", "2026-11-01T00:00:00"):
            with self.subTest(date=value):
                self.assertEqual(filter_events(self.events, date=value), [])

    def test_input_list_and_dictionaries_are_unchanged(self):
        before = deepcopy(self.events)
        originals = list(self.events)
        for filters in ({}, {"category": "music"}, {"date": "2026-11-02"}):
            with self.subTest(filters=filters):
                result = filter_events(self.events, **filters)
                self.assertEqual(self.events, before)
                for event, original in zip(self.events, originals):
                    self.assertIs(event, original)
                for event in result:
                    self.assertTrue(any(event is original for original in originals))

    def test_empty_catalog(self):
        self.assertEqual(filter_events([]), [])
        self.assertEqual(filter_events([], category="Music", date="2026-11-01"), [])


if __name__ == "__main__":
    unittest.main()

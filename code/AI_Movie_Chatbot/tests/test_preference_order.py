# AI-USAGE SUMMARY
# Authors: Yung Cheng Chiu
# Tools: Claude (Anthropic), prompted by Yung Cheng Chiu
# Overall AI Contribution: ~90%
# AI-Assisted Areas: FV-127 preference-order test cases
# Human Contributions: Yung Cheng Chiu: requirements from Jira FV-127, rule decision (preferred categories first, nothing removed), prompts, running the tests, review of results
# Notes/Verification: run with python -m unittest tests.test_preference_order -v

"""Behavioral checks for FV-127, using the catalog fixtures and a fixed clock.

Rule under test: when the parsed chat request has no category, events in the
user's preferred categories come first and every other event follows; both
groups keep their existing (start-time) order and nothing is dropped. When the
request names a category, the list is left as it is.
"""

import json
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.event_catalog import remove_ended, sort_by_start
from app.preference_order import order_by_preferences

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"


def upcoming_sorted() -> list[dict]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        events = json.load(fixture_file)["events"]
    return sort_by_start(remove_ended(events, NOW))


def ids(events: list[dict]) -> list[str]:
    return [event["id"] for event in events]


def categories(events: list[dict]) -> list[str]:
    return [event["category"] for event in events]


class OrderByPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.events = upcoming_sorted()
        self.assertEqual(len(self.events), 12)  # guard: fixture unchanged

    def test_preferred_category_comes_first_and_nothing_is_dropped(self):
        result = order_by_preferences(self.events, ["Arts"])
        arts = [event for event in self.events if event["category"] == "Arts"]
        others = [event for event in self.events if event["category"] != "Arts"]
        self.assertEqual(ids(result), ids(arts) + ids(others))
        self.assertEqual(sorted(ids(result)), sorted(ids(self.events)))

    def test_each_group_keeps_its_start_time_order(self):
        result = order_by_preferences(self.events, ["Music", "Food"])
        preferred = [event for event in result if event["category"] in ("Music", "Food")]
        rest = [event for event in result if event["category"] not in ("Music", "Food")]
        self.assertEqual(preferred, sort_by_start(preferred))
        self.assertEqual(rest, sort_by_start(rest))
        self.assertEqual(result, preferred + rest)

    def test_several_preferences_are_not_ranked_among_themselves(self):
        # Preferences are a set, not a ranking: Music and Food events are
        # interleaved by start time, not grouped Music-then-Food.
        result = order_by_preferences(self.events, ["Music", "Food"])
        wanted = [e for e in self.events if e["category"] in ("Music", "Food")]
        head = categories(result)[:len(wanted)]
        self.assertEqual(set(head), {"Music", "Food"})
        self.assertEqual(head, categories(sort_by_start(wanted)))
        self.assertNotEqual(head, sorted(head))  # really interleaved, not grouped

    def test_requested_category_disables_preferences(self):
        for requested in ("Music", "Arts", "Outdoors"):
            with self.subTest(requested=requested):
                result = order_by_preferences(self.events, ["Social"], requested_category=requested)
                self.assertEqual(ids(result), ids(self.events))

    def test_no_preferences_leaves_order_unchanged(self):
        for preferences in (None, [], ()):
            with self.subTest(preferences=preferences):
                self.assertEqual(ids(order_by_preferences(self.events, preferences)),
                                 ids(self.events))

    def test_preferences_matching_no_event_leave_order_unchanged(self):
        self.assertEqual(ids(order_by_preferences(self.events, ["Sports", "Movies"])),
                         ids(self.events))

    def test_category_match_ignores_case(self):
        expected = ids(order_by_preferences(self.events, ["Outdoors"]))
        for spelling in ("outdoors", "OUTDOORS", "OutDoors"):
            with self.subTest(spelling=spelling):
                self.assertEqual(ids(order_by_preferences(self.events, [spelling])), expected)

    def test_all_categories_preferred_leaves_order_unchanged(self):
        every = ["Music", "Arts", "Food", "Outdoors", "Social"]
        self.assertEqual(ids(order_by_preferences(self.events, every)), ids(self.events))

    def test_single_event_and_empty_list(self):
        self.assertEqual(order_by_preferences([], ["Music"]), [])
        only = self.events[:1]
        self.assertEqual(order_by_preferences(only, ["Music"]), only)
        self.assertEqual(order_by_preferences(only, ["Social"]), only)

    def test_returns_a_new_list_and_leaves_input_unchanged(self):
        before = deepcopy(self.events)
        originals = list(self.events)
        for preferences, requested in ((["Arts"], None), (["Arts"], "Music"), (None, None)):
            with self.subTest(preferences=preferences, requested=requested):
                result = order_by_preferences(self.events, preferences, requested)
                self.assertIsNot(result, self.events)
                self.assertEqual(self.events, before)
                for event in result:
                    self.assertTrue(any(event is original for original in originals))

    def test_example_from_the_ticket(self):
        # "Something fun" with Music preferences: the two Music events lead,
        # then everything else in start order.
        result = order_by_preferences(self.events, ["Music"], requested_category=None)
        self.assertEqual(ids(result)[:2], ["fixture-06", "fixture-10"])
        self.assertEqual(ids(result)[2:], [i for i in ids(self.events)
                                           if i not in ("fixture-06", "fixture-10")])


if __name__ == "__main__":
    unittest.main()
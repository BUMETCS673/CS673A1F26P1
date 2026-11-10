
import json
import unittest
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.event_catalog import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    find_event,
    paginate,
    remove_ended,
    sort_by_start,
)

BOSTON = ZoneInfo("America/New_York")
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=BOSTON)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"

ENDED_IDS = {"fixture-01", "fixture-02"}
# Every event still visible at NOW, in the order the API should list them.
UPCOMING_IN_ORDER = [
    "fixture-03",  # in progress (11:00-13:00)
    "fixture-04",  # starts 12:01
    "fixture-05",  # 11/16 19:00, same start as fixture-06; id sorts first
    "fixture-06",
    "fixture-07",
    "fixture-08",
    "fixture-09",
    "fixture-10",
    "fixture-11",
    "fixture-12",
    "fixture-14",  # 2027-03-13, UTC-05:00
    "fixture-13",  # 2027-03-20, UTC-04:00 after daylight saving time starts
]


def load_fixture_events() -> list[dict]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)["events"]


def ids(events: list[dict]) -> list[str]:
    return [event["id"] for event in events]


def upcoming_sorted(now: datetime = NOW) -> list[dict]:
    return sort_by_start(remove_ended(load_fixture_events(), now))


def collect_all_pages(events: list[dict], limit: int) -> list[list[str]]:
    """Follow next_offset like the "Load more" button; return each page's IDs."""
    pages, offset = [], 0
    for _ in range(len(events) + 2):  # guard against a next_offset that never ends
        page = paginate(events, limit=limit, offset=offset)
        pages.append(ids(page["events"]))
        offset = page["next_offset"]
        if offset is None:
            return pages
    raise AssertionError("next_offset never became None")


class FixtureSanityTests(unittest.TestCase):
    """Fail early with a clear message if someone edits the fixture file."""

    def test_fixture_ids_are_unique_and_complete(self):
        events = load_fixture_events()
        self.assertEqual(len(events), len(set(ids(events))))
        self.assertEqual(set(ids(events)), ENDED_IDS | set(UPCOMING_IN_ORDER))

    def test_fixture_file_is_not_already_sorted(self):
        self.assertNotEqual(ids(load_fixture_events()), UPCOMING_IN_ORDER)


class RemoveEndedTests(unittest.TestCase):
    def setUp(self):
        self.events = load_fixture_events()

    def test_keeps_exactly_the_upcoming_and_in_progress_events(self):
        self.assertEqual(set(ids(remove_ended(self.events, NOW))), set(UPCOMING_IN_ORDER))

    def test_event_that_ended_yesterday_is_removed(self):
        self.assertNotIn("fixture-01", ids(remove_ended(self.events, NOW)))

    def test_event_ending_exactly_at_now_is_removed(self):
        self.assertNotIn("fixture-02", ids(remove_ended(self.events, NOW)))

    def test_event_in_progress_is_kept(self):
        self.assertIn("fixture-03", ids(remove_ended(self.events, NOW)))

    def test_event_one_second_before_its_end_is_kept(self):
        almost_over = datetime(2026, 11, 15, 11, 59, 59, tzinfo=BOSTON)
        self.assertIn("fixture-02", ids(remove_ended(self.events, almost_over)))

    def test_keeps_the_original_order(self):
        result = ids(remove_ended(self.events, NOW))
        expected = [event_id for event_id in ids(self.events) if event_id not in ENDED_IDS]
        self.assertEqual(result, expected)

    def test_same_instant_in_another_time_zone_gives_the_same_result(self):
        # A server or teammate in Taipei must see the same Boston catalog.
        now_in_taipei = NOW.astimezone(ZoneInfo("Asia/Taipei"))
        self.assertEqual(remove_ended(self.events, now_in_taipei),
                         remove_ended(self.events, NOW))

    def test_later_reference_time_hides_more_events(self):
        after_new_year = datetime(2027, 1, 1, 9, 0, tzinfo=BOSTON)
        self.assertEqual(set(ids(remove_ended(self.events, after_new_year))),
                         {"fixture-12", "fixture-13", "fixture-14"})

    def test_everything_ended_returns_empty_list(self):
        self.assertEqual(remove_ended(self.events, datetime(2028, 1, 1, tzinfo=BOSTON)), [])

    def test_empty_catalog(self):
        self.assertEqual(remove_ended([], NOW), [])

    def test_now_without_time_zone_is_rejected(self):
        with self.assertRaises(ValueError):
            remove_ended(self.events, datetime(2026, 11, 15, 12, 0))

    def test_event_time_without_offset_is_rejected(self):
        # "2026-11-20T18:00:00" is ambiguous: Boston time? UTC? Refuse to guess.
        bad = [{"id": "x", "start": "2026-11-20T18:00:00", "end": "2026-11-20T20:00:00"}]
        with self.assertRaises(ValueError):
            remove_ended(bad, NOW)

    def test_unreadable_event_time_is_rejected(self):
        bad = [{"id": "x", "start": "2026-11-20T18:00:00-05:00", "end": "6:00 PM"}]
        with self.assertRaises(ValueError):
            remove_ended(bad, NOW)

    def test_input_list_and_dictionaries_are_unchanged(self):
        before = deepcopy(self.events)
        originals = list(self.events)
        result = remove_ended(self.events, NOW)
        self.assertIsNot(result, self.events)
        self.assertEqual(self.events, before)
        for event, original in zip(self.events, originals):
            self.assertIs(event, original)
        for event in result:
            self.assertTrue(any(event is original for original in originals))


class SortByStartTests(unittest.TestCase):
    def test_sorts_fixture_by_start_then_id(self):
        result = sort_by_start(remove_ended(load_fixture_events(), NOW))
        self.assertEqual(ids(result), UPCOMING_IN_ORDER)

    def test_same_start_time_is_ordered_by_id_whatever_the_input_order(self):
        events = [
            {"id": "b", "start": "2026-11-16T19:00:00-05:00", "end": "2026-11-16T21:00:00-05:00"},
            {"id": "c", "start": "2026-11-16T19:00:00-05:00", "end": "2026-11-16T20:00:00-05:00"},
            {"id": "a", "start": "2026-11-16T19:00:00-05:00", "end": "2026-11-16T22:00:00-05:00"},
        ]
        for order in ([0, 1, 2], [2, 1, 0], [1, 2, 0]):
            with self.subTest(order=order):
                shuffled = [events[index] for index in order]
                self.assertEqual(ids(sort_by_start(shuffled)), ["a", "b", "c"])

    def test_compares_moments_in_time_not_text(self):
        # 22:30Z is 5:30 PM in Boston, so it comes before 6:00 PM Boston time,
        # although its text would sort after it.
        events = [
            {"id": "boston-6pm", "start": "2026-11-20T18:00:00-05:00",
             "end": "2026-11-20T20:00:00-05:00"},
            {"id": "utc-1030pm", "start": "2026-11-20T22:30:00+00:00",
             "end": "2026-11-20T23:30:00+00:00"},
        ]
        self.assertEqual(ids(sort_by_start(events)), ["utc-1030pm", "boston-6pm"])

    def test_events_on_both_sides_of_daylight_saving_time(self):
        events = [
            {"id": "after-dst", "start": "2027-03-14T12:00:00-04:00",
             "end": "2027-03-14T13:00:00-04:00"},
            {"id": "before-dst", "start": "2027-03-13T12:00:00-05:00",
             "end": "2027-03-13T13:00:00-05:00"},
        ]
        self.assertEqual(ids(sort_by_start(events)), ["before-dst", "after-dst"])

    def test_already_sorted_list_keeps_its_order(self):
        ordered = upcoming_sorted()
        self.assertEqual(ids(sort_by_start(ordered)), UPCOMING_IN_ORDER)

    def test_empty_catalog(self):
        self.assertEqual(sort_by_start([]), [])

    def test_event_time_without_offset_is_rejected(self):
        bad = [{"id": "x", "start": "2026-11-20T18:00:00", "end": "2026-11-20T20:00:00-05:00"}]
        with self.assertRaises(ValueError):
            sort_by_start(bad)

    def test_input_list_and_dictionaries_are_unchanged(self):
        events = load_fixture_events()
        before = deepcopy(events)
        originals = list(events)
        result = sort_by_start(events)
        self.assertIsNot(result, events)
        self.assertEqual(events, before)
        for event, original in zip(events, originals):
            self.assertIs(event, original)
        for event in result:
            self.assertTrue(any(event is original for original in originals))


class FindEventTests(unittest.TestCase):
    """FV-122: the helper behind GET /api/events/{id}."""

    def setUp(self):
        self.events = load_fixture_events()

    def test_returns_the_matching_event_itself(self):
        found = find_event(self.events, "fixture-07")
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], "fixture-07")
        self.assertTrue(any(found is event for event in self.events))

    def test_unknown_id_returns_none(self):
        # The API turns None into HTTP 404.
        self.assertIsNone(find_event(self.events, "fixture-99"))

    def test_id_must_match_exactly(self):
        for event_id in ("FIXTURE-07", " fixture-07", "fixture-7", "fixture", ""):
            with self.subTest(event_id=event_id):
                self.assertIsNone(find_event(self.events, event_id))

    def test_finds_events_in_any_position(self):
        for event in self.events:
            with self.subTest(event_id=event["id"]):
                self.assertIs(find_event(self.events, event["id"]), event)

    def test_event_with_missing_location_is_returned_as_is(self):
        # The frontend shows null as "unavailable"; the backend must not drop it.
        found = find_event(self.events, "fixture-09")
        self.assertIn("location", found)
        self.assertIsNone(found["location"])

    def test_empty_catalog(self):
        self.assertIsNone(find_event([], "fixture-07"))

    def test_input_list_and_dictionaries_are_unchanged(self):
        before = deepcopy(self.events)
        find_event(self.events, "fixture-07")
        find_event(self.events, "fixture-99")
        self.assertEqual(self.events, before)


class MissingValueTests(unittest.TestCase):
    """FV-122: events with null optional fields still flow through the list."""

    def test_event_with_null_location_stays_visible_and_unchanged(self):
        visible = upcoming_sorted()
        event = find_event(visible, "fixture-09")
        self.assertIsNotNone(event)
        self.assertIsNone(event["location"])

    def test_event_with_null_location_appears_in_its_page(self):
        pages = collect_all_pages(upcoming_sorted(), limit=5)
        self.assertIn("fixture-09", pages[1])


class PaginateTests(unittest.TestCase):
    """FV-123: limit/offset pages behind the "Load more" button."""

    def setUp(self):
        self.events = upcoming_sorted()

    def test_first_page_returns_the_first_events_and_the_next_offset(self):
        page = paginate(self.events, limit=5)
        self.assertEqual(set(page), {"events", "next_offset"})
        self.assertEqual(ids(page["events"]), UPCOMING_IN_ORDER[:5])
        self.assertEqual(page["next_offset"], 5)

    def test_following_next_offset_returns_every_event_once_in_order(self):
        pages = collect_all_pages(self.events, limit=5)
        self.assertEqual(pages, [UPCOMING_IN_ORDER[0:5],
                                 UPCOMING_IN_ORDER[5:10],
                                 UPCOMING_IN_ORDER[10:12]])

    def test_no_duplicates_or_gaps_for_every_page_size(self):
        for limit in range(1, len(UPCOMING_IN_ORDER) + 2):
            with self.subTest(limit=limit):
                pages = collect_all_pages(self.events, limit=limit)
                flat = [event_id for page in pages for event_id in page]
                self.assertEqual(len(flat), len(set(flat)), "duplicate IDs across pages")
                self.assertEqual(flat, UPCOMING_IN_ORDER)
                self.assertTrue(all(0 < len(page) <= limit for page in pages))

    def test_last_page_has_no_next_offset(self):
        page = paginate(self.events, limit=5, offset=10)
        self.assertEqual(ids(page["events"]), UPCOMING_IN_ORDER[10:])
        self.assertIsNone(page["next_offset"])

    def test_exact_multiple_does_not_end_with_an_empty_page(self):
        pages = collect_all_pages(self.events, limit=6)
        self.assertEqual(len(pages), 2)

    def test_offset_at_or_past_the_end_returns_an_empty_page(self):
        for offset in (len(self.events), len(self.events) + 1, 1000):
            with self.subTest(offset=offset):
                self.assertEqual(paginate(self.events, limit=5, offset=offset),
                                 {"events": [], "next_offset": None})

    def test_limit_larger_than_catalog_returns_one_page(self):
        page = paginate(self.events, limit=MAX_PAGE_SIZE)
        self.assertEqual(ids(page["events"]), UPCOMING_IN_ORDER)
        self.assertIsNone(page["next_offset"])

    def test_defaults(self):
        page = paginate(self.events)
        self.assertEqual(ids(page["events"]), UPCOMING_IN_ORDER[:DEFAULT_PAGE_SIZE])

    def test_empty_catalog(self):
        # The frontend shows "No upcoming events" for this response.
        self.assertEqual(paginate([], limit=5), {"events": [], "next_offset": None})

    def test_limit_boundaries(self):
        for limit in (1, MAX_PAGE_SIZE):
            with self.subTest(limit=limit):
                paginate(self.events, limit=limit)  # accepted, no error
        for limit in (0, -1, MAX_PAGE_SIZE + 1):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                paginate(self.events, limit=limit)

    def test_negative_offset_is_rejected(self):
        for offset in (-1, -5):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                paginate(self.events, limit=5, offset=offset)

    def test_event_ending_between_requests_causes_no_duplicate(self):
        # Page 1 is loaded at noon and page 2 at 2 PM, after fixture-03 and
        # fixture-04 have ended. The pages must not repeat any event.
        # Known limitation of limit/offset: the list shifts, so fixture-06 and
        # fixture-07 are skipped. Acceptable for a static catalog; a cursor
        # (after the last start time and id) would avoid it if this matters later.
        first = paginate(upcoming_sorted(NOW), limit=3)
        later = NOW + timedelta(hours=2)
        second = paginate(upcoming_sorted(later), limit=3, offset=first["next_offset"])
        self.assertFalse(set(ids(first["events"])) & set(ids(second["events"])))

    def test_input_list_is_unchanged(self):
        before = deepcopy(self.events)
        paginate(self.events, limit=5, offset=5)
        self.assertEqual(self.events, before)


if __name__ == "__main__":
    unittest.main()
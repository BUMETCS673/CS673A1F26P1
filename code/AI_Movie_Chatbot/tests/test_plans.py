# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: My Plans route tests with the storage replaced by a fake (FV-95)
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: all tests pass without a database; tests/live_plans.py covers PostgreSQL

"""My Plans API tests. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v.

The storage module is replaced by an in-memory fake, so these need no database.
tests/live_plans.py runs the same flow against PostgreSQL with two accounts.
"""

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

import psycopg
from fastapi.testclient import TestClient

from app import plans
from app.main import create_app
from app.routes import events as events_route
from app.routes.auth import require_user

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "catalog_events.json"
BOSTON = ZoneInfo("America/New_York")
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=BOSTON)


class FakeStorage:
    """Stores (user_id, event_id) pairs like the user_plans table, primary key included."""

    def __init__(self):
        self.rows = {}
        self.clock = datetime(2026, 11, 14, 20, 0, tzinfo=timezone.utc)

    def list_saved(self, user_id):
        rows = [
            {"event_id": event_id, "saved_at": saved_at}
            for (owner, event_id), saved_at in self.rows.items() if owner == user_id
        ]
        return sorted(rows, key=lambda row: (row["saved_at"], row["event_id"]))

    def save(self, user_id, event_id):
        self.clock += timedelta(minutes=1)
        self.rows.setdefault((user_id, event_id), self.clock)

    def remove(self, user_id, event_id):
        self.rows.pop((user_id, event_id), None)


class PlansApiTests(unittest.TestCase):
    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            self.catalog = list(json.load(fixture_file)["events"])
        self.now = NOW
        self.storage = FakeStorage()
        patches = [
            mock.patch.object(events_route, "load_sample_events", lambda: tuple(self.catalog)),
            mock.patch.object(events_route, "current_time", lambda: self.now),
        ]
        for name in ("list_saved", "save", "remove"):
            patches.append(mock.patch.object(plans, name, getattr(self.storage, name)))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.application = create_app()
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)
        self.sign_in_as(1)

    def sign_in_as(self, user_id):
        self.application.dependency_overrides[require_user] = lambda: {"id": user_id}

    def listing(self):
        response = self.client.get("/api/plans")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def saved_ids(self):
        return [plan["event"]["id"] for plan in self.listing()["plans"]]

    def save(self, event_id, expected=204):
        response = self.client.put(f"/api/plans/{event_id}")
        self.assertEqual(response.status_code, expected, response.text)
        return response

    def test_plans_require_login(self):
        self.application.dependency_overrides.clear()
        for method, path in (("GET", "/api/plans"), ("PUT", "/api/plans/fixture-06"),
                             ("DELETE", "/api/plans/fixture-06")):
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, path).status_code, 401)
        self.assertEqual(self.storage.rows, {})

    def test_new_account_has_no_plans(self):
        self.assertEqual(self.listing(), {"plans": [], "unavailable_count": 0})

    def test_save_returns_the_full_event_with_saved_time(self):
        response = self.save("fixture-06")
        self.assertEqual(response.content, b"")
        (plan,) = self.listing()["plans"]
        fixture = next(event for event in self.catalog if event["id"] == "fixture-06")
        self.assertEqual(plan["event"], fixture)
        self.assertFalse(plan["ended"])
        self.assertEqual(datetime.fromisoformat(plan["saved_at"]), self.storage.rows[(1, "fixture-06")])
        self.assertEqual(set(plan), {"event", "saved_at", "ended"})

    def test_saving_twice_keeps_one_entry_and_the_first_saved_time(self):
        self.save("fixture-06")
        first = self.listing()["plans"][0]["saved_at"]
        self.save("fixture-06")
        self.assertEqual(self.saved_ids(), ["fixture-06"])
        self.assertEqual(self.listing()["plans"][0]["saved_at"], first)

    def test_plans_are_listed_by_start_time_not_save_order(self):
        for event_id in ("fixture-13", "fixture-10", "fixture-06", "fixture-05", "fixture-11"):
            self.save(event_id)
        # fixture-05 and fixture-06 start at the same moment; the ID breaks the tie.
        self.assertEqual(self.saved_ids(), ["fixture-05", "fixture-06", "fixture-10", "fixture-11", "fixture-13"])

    def test_unknown_event_is_404_and_not_stored(self):
        for event_id in ("no-such-event", "FIXTURE-06", "fixture-06 ", "fixture-0"):
            with self.subTest(event_id=event_id):
                response = self.save(event_id, expected=404)
                self.assertEqual(response.json()["detail"], "Event not found")
        self.assertEqual(self.storage.rows, {})

    def test_ended_events_cannot_be_saved(self):
        # fixture-01 ended yesterday; fixture-02 ends exactly at NOW, which counts as ended.
        for event_id in ("fixture-01", "fixture-02"):
            with self.subTest(event_id=event_id):
                response = self.save(event_id, expected=409)
                self.assertEqual(response.json()["detail"], "This event has already ended.")
        self.assertEqual(self.storage.rows, {})

    def test_an_event_in_progress_can_still_be_saved(self):
        self.save("fixture-03")  # 11:00-13:00 on the reference day
        self.assertEqual(self.saved_ids(), ["fixture-03"])

    def test_saved_events_that_end_stay_listed_as_ended(self):
        self.save("fixture-03")
        self.save("fixture-06")
        self.now = datetime(2026, 11, 16, 21, 0, tzinfo=BOSTON)  # fixture-06 ends at 21:00
        listing = self.listing()["plans"]
        self.assertEqual([(plan["event"]["id"], plan["ended"]) for plan in listing],
                         [("fixture-03", True), ("fixture-06", True)])
        self.now = datetime(2026, 11, 16, 20, 59, tzinfo=BOSTON)
        self.assertEqual([plan["ended"] for plan in self.listing()["plans"]], [True, False])

    def test_events_removed_from_the_catalog_are_counted_not_shown(self):
        self.save("fixture-06")
        self.save("fixture-10")
        self.catalog = [event for event in self.catalog if event["id"] != "fixture-10"]
        self.assertEqual(self.listing()["unavailable_count"], 1)
        self.assertEqual(self.saved_ids(), ["fixture-06"])
        # The stale row can still be removed.
        self.assertEqual(self.client.delete("/api/plans/fixture-10").status_code, 204)
        self.assertEqual(self.listing()["unavailable_count"], 0)

    def test_plans_show_current_catalog_details(self):
        self.save("fixture-06")
        self.catalog = [dict(event, title="Renamed open mic") if event["id"] == "fixture-06" else event
                        for event in self.catalog]
        self.assertEqual(self.listing()["plans"][0]["event"]["title"], "Renamed open mic")

    def test_remove_is_idempotent_and_ended_events_can_be_removed(self):
        self.save("fixture-06")
        self.save("fixture-10")
        for _ in range(2):
            response = self.client.delete("/api/plans/fixture-06")
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.content, b"")
        self.assertEqual(self.saved_ids(), ["fixture-10"])
        self.assertEqual(self.client.delete("/api/plans/no-such-event").status_code, 204)
        self.now = datetime(2027, 1, 1, tzinfo=BOSTON)  # fixture-10 has ended
        self.assertEqual(self.client.delete("/api/plans/fixture-10").status_code, 204)
        self.assertEqual(self.saved_ids(), [])

    def test_plans_are_private_to_each_account(self):
        self.save("fixture-06")
        self.save("fixture-10")
        self.sign_in_as(2)
        self.assertEqual(self.saved_ids(), [])
        self.save("fixture-10")
        # User 2 removing fixture-06 (which only user 1 saved) and fixture-10 changes only user 2.
        self.client.delete("/api/plans/fixture-06")
        self.client.delete("/api/plans/fixture-10")
        self.assertEqual(self.saved_ids(), [])
        self.sign_in_as(1)
        self.assertEqual(self.saved_ids(), ["fixture-06", "fixture-10"])

    def test_query_parameters_cannot_choose_another_account(self):
        self.save("fixture-06")
        self.sign_in_as(2)
        self.client.delete("/api/plans/fixture-06", params={"user_id": 1})
        self.client.put("/api/plans/fixture-10", params={"user_id": 1})
        spoofed = self.client.get("/api/plans", params={"user_id": 1}).json()["plans"]
        self.assertEqual([plan["event"]["id"] for plan in spoofed], ["fixture-10"])
        self.assertEqual(set(self.storage.rows), {(1, "fixture-06"), (2, "fixture-10")})

    def test_overlong_event_id_is_rejected_before_storage(self):
        long_id = "x" * 101
        for method in ("PUT", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, f"/api/plans/{long_id}").status_code, 422)

    def test_markup_in_event_id_is_just_an_unknown_id(self):
        response = self.client.put("/api/plans/%3Cscript%3Ealert(1)%3C%2Fscript%3E")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("<script>", response.text)

    def test_database_failures_return_503_without_details(self):
        failure = mock.Mock(side_effect=psycopg.OperationalError("password=secret"))
        for name, method, path in (("list_saved", "GET", "/api/plans"),
                                   ("save", "PUT", "/api/plans/fixture-06"),
                                   ("remove", "DELETE", "/api/plans/fixture-06")):
            with self.subTest(method=method), mock.patch.object(plans, name, failure):
                response = self.client.request(method, path)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["detail"], "My Plans is unavailable right now. Please try again.")
                self.assertNotIn("secret", response.text)

    def test_ended_check_happens_before_storage_is_touched(self):
        with mock.patch.object(plans, "save", side_effect=AssertionError("must not save")):
            self.save("fixture-01", expected=409)
            self.save("missing", expected=404)


if __name__ == "__main__":
    unittest.main()

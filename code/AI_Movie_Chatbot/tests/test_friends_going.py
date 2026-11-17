# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over "friends going" from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: friends going route tests with the storage replaced by a fake
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: all tests pass without a database; tests/live_friends_going.py covers the SQL

"""Friends going API tests. Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v."""

import json
import unittest
from datetime import datetime, timezone
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
NOW = datetime(2026, 11, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))
USERS = {
    1: {"id": 1, "username": "alex", "display_name": "Alex"},
    2: {"id": 2, "username": "sam", "display_name": "Sam"},
    3: {"id": 3, "username": "pat", "display_name": None},
    4: {"id": 4, "username": "Bea", "display_name": "Bea"},
}


class FakeStorage:
    """Plans and follows in memory, with the same mutual-follow rule as the SQL."""

    def __init__(self):
        self.saved = set()     # (user_id, event_id)
        self.follows = set()   # (follower_id, followed_id)

    def mutual(self, a, b):
        return (a, b) in self.follows and (b, a) in self.follows

    def list_saved(self, user_id):
        saved_at = datetime(2026, 11, 14, tzinfo=timezone.utc)
        return [{"event_id": e, "saved_at": saved_at} for (u, e) in sorted(self.saved) if u == user_id]

    def friends_going(self, user_id, event_id):
        going = [USERS[u] for (u, e) in self.saved if e == event_id and self.mutual(user_id, u)]
        return sorted(going, key=lambda user: (user["username"].lower(), user["id"]))

    def mutual_friend(self, user_id, friend_id):
        return USERS.get(friend_id) if self.mutual(user_id, friend_id) else None


class FriendsGoingTests(unittest.TestCase):
    def setUp(self):
        with FIXTURES.open(encoding="utf-8") as fixture_file:
            self.catalog = list(json.load(fixture_file)["events"])
        self.storage = FakeStorage()
        patches = [
            mock.patch.object(events_route, "load_sample_events", lambda: tuple(self.catalog)),
            mock.patch.object(events_route, "current_time", lambda: NOW),
        ]
        for name in ("list_saved", "friends_going", "mutual_friend"):
            patches.append(mock.patch.object(plans, name, getattr(self.storage, name)))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.application = create_app()
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)
        self.sign_in_as(1)
        # Alex and Sam, and Alex and Bea, are friends. Pat follows Alex, but not back.
        self.storage.follows |= {(1, 2), (2, 1), (1, 4), (4, 1), (3, 1)}

    def sign_in_as(self, user_id):
        self.application.dependency_overrides[require_user] = lambda: {"id": user_id}

    def going(self, event_id="fixture-06"):
        response = self.client.get(f"/api/events/{event_id}/friends-going")
        self.assertEqual(response.status_code, 200, response.text)
        return [friend["username"] for friend in response.json()["friends"]]

    def test_requires_login(self):
        self.application.dependency_overrides.clear()
        for path in ("/api/events/fixture-06/friends-going", "/api/friends/2/plans"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)

    def test_only_mutual_follows_who_saved_the_event_are_listed(self):
        self.storage.saved |= {(2, "fixture-06"), (3, "fixture-06"), (4, "fixture-06"), (2, "fixture-10")}
        # Sorted by username ignoring case; Pat (one-way follower) is not included.
        self.assertEqual(self.going(), ["Bea", "sam"])
        response = self.client.get("/api/events/fixture-06/friends-going").json()
        self.assertEqual(response["friends"][1], USERS[2])

    def test_nobody_going_is_an_empty_list(self):
        self.assertEqual(self.going(), [])

    def test_own_plan_does_not_count(self):
        self.storage.saved.add((1, "fixture-06"))
        self.assertEqual(self.going(), [])

    def test_one_way_follows_see_nothing_in_either_direction(self):
        self.storage.saved |= {(1, "fixture-06"), (3, "fixture-06")}
        self.assertEqual(self.going(), [])  # Alex does not follow Pat back
        self.sign_in_as(3)
        self.assertEqual(self.going(), [])  # Pat follows Alex, but Alex does not follow Pat

    def test_unfollowing_removes_access_immediately(self):
        self.storage.saved.add((2, "fixture-06"))
        self.assertEqual(self.going(), ["sam"])
        self.storage.follows.discard((2, 1))
        self.assertEqual(self.going(), [])
        self.assertEqual(self.client.get("/api/friends/2/plans").status_code, 404)

    def test_unknown_event_is_404(self):
        response = self.client.get("/api/events/no-such-event/friends-going")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get(f"/api/events/{'x' * 101}/friends-going").status_code, 422)

    def test_friend_plans_lists_upcoming_saved_events_in_start_order(self):
        # fixture-01 has ended; fixture-03 is in progress; gone-1 left the catalog.
        self.storage.saved |= {(2, e) for e in ("fixture-13", "fixture-01", "fixture-06", "fixture-03", "gone-1")}
        response = self.client.get("/api/friends/2/plans")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["friend"], USERS[2])
        self.assertEqual([plan["event"]["id"] for plan in body["plans"]], ["fixture-03", "fixture-06", "fixture-13"])
        self.assertEqual(set(body["plans"][0]), {"event"})  # no saved_at for other people's plans

    def test_friend_plans_are_404_for_anyone_not_a_mutual_follow(self):
        self.storage.saved |= {(3, "fixture-06"), (2, "fixture-06")}
        for user_id in (3, 1, 99, 2_147_483_647):  # one-way follower, yourself, unknown, max ID
            with self.subTest(user_id=user_id):
                response = self.client.get(f"/api/friends/{user_id}/plans")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()["detail"], "Friend not found")
        self.sign_in_as(3)  # Pat follows Alex one way: still no access to Alex's plans
        self.assertEqual(self.client.get("/api/friends/1/plans").status_code, 404)
        for bad in ("0", "-1", "abc", "2147483648"):
            with self.subTest(bad=bad):
                self.assertEqual(self.client.get(f"/api/friends/{bad}/plans").status_code, 422)

    def test_database_failures_return_503_without_details(self):
        failure = mock.Mock(side_effect=psycopg.OperationalError("password=secret"))
        for name, path in (("friends_going", "/api/events/fixture-06/friends-going"),
                           ("mutual_friend", "/api/friends/2/plans"),
                           ("list_saved", "/api/friends/2/plans")):
            with self.subTest(name=name), mock.patch.object(plans, name, failure):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("secret", response.text)


if __name__ == "__main__":
    unittest.main()

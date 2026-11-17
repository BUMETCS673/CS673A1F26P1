# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over "friends going" from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: three-account friends going checks against PostgreSQL
# Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
# Notes/Verification: run against a PostgreSQL database with all migrations applied (also run by the PR checks)

"""Friends going with real sessions, follows, and plans, using three accounts.

Run from AI_Movie_Chatbot with the database variables set (see README):
python -m unittest discover -s tests -p live_friends_going.py -v
"""

import secrets
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import create_app
from app.routes import events as events_route

BEFORE_THE_CATALOG = datetime(2026, 11, 1, 12, 0, tzinfo=ZoneInfo("America/New_York"))


class LiveFriendsGoingTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(events_route, "current_time", lambda: BEFORE_THE_CATALOG)
        patcher.start()
        self.addCleanup(patcher.stop)
        catalog = sorted(events_route.load_sample_events(), key=lambda event: (event["start"], event["id"]))
        self.event, self.other = catalog[0]["id"], catalog[1]["id"]

    def account(self, name):
        client = TestClient(create_app())
        self.addCleanup(client.close)
        username = f"{name}_{secrets.token_hex(4)}"
        response = client.post("/api/auth/register", json={
            "username": username, "display_name": name.title(), "email": f"{username}@example.com",
            "password": "live test password", "activity_preferences": ["Music"],
        })
        self.assertEqual(response.status_code, 201, response.text)
        profile = {key: response.json()[key] for key in ("id", "username", "display_name")}
        self.addCleanup(self.delete_account, profile["id"])
        login = {"username": username, "password": "live test password"}
        self.assertEqual(client.post("/api/auth/login", json=login).status_code, 200)
        return client, profile

    def delete_account(self, user_id):
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = %s", (user_id,))

    def going(self, client, event_id=None):
        response = client.get(f"/api/events/{event_id or self.event}/friends-going")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["friends"]

    def test_requires_login(self):
        with TestClient(create_app()) as guest:
            self.assertEqual(guest.get(f"/api/events/{self.event}/friends-going").status_code, 401)
            self.assertEqual(guest.get("/api/friends/1/plans").status_code, 401)

    def test_mutual_follows_only_and_unfollow_removes_access(self):
        alex, alex_profile = self.account("alex")
        sam, sam_profile = self.account("sam")
        pat, pat_profile = self.account("pat")

        for client in (sam, pat):
            self.assertEqual(client.put(f"/api/plans/{self.event}").status_code, 204)
        self.assertEqual(sam.put(f"/api/plans/{self.other}").status_code, 204)

        # Nobody follows anybody yet.
        self.assertEqual(self.going(alex), [])
        self.assertEqual(alex.get(f"/api/friends/{sam_profile['id']}/plans").status_code, 404)

        # Alex follows Sam, but not back yet: still nothing.
        alex.put(f"/api/following/{sam_profile['id']}")
        self.assertEqual(self.going(alex), [])
        self.assertEqual(alex.get(f"/api/friends/{sam_profile['id']}/plans").status_code, 404)

        # Sam follows back: now they are friends, in both directions.
        sam.put(f"/api/following/{alex_profile['id']}")
        self.assertEqual(self.going(alex), [sam_profile])
        plans = alex.get(f"/api/friends/{sam_profile['id']}/plans").json()
        self.assertEqual(plans["friend"], sam_profile)
        self.assertEqual([plan["event"]["id"] for plan in plans["plans"]], sorted(
            [self.event, self.other], key=lambda event_id: [e["start"] for e in events_route.load_sample_events()
                                                            if e["id"] == event_id][0]))
        self.assertEqual(self.going(sam), [])  # Alex has saved nothing
        alex.put(f"/api/plans/{self.event}")
        self.assertEqual(self.going(sam), [alex_profile])

        # Pat follows Alex one way and saved the same event: invisible both ways.
        pat.put(f"/api/following/{alex_profile['id']}")
        self.assertEqual(self.going(alex), [sam_profile])
        self.assertEqual(self.going(pat), [])
        self.assertEqual(pat.get(f"/api/friends/{alex_profile['id']}/plans").status_code, 404)
        self.assertEqual(pat.get(f"/api/friends/{sam_profile['id']}/plans").status_code, 404)

        # Unfollowing from either side removes access immediately.
        sam.delete(f"/api/following/{alex_profile['id']}")
        self.assertEqual(self.going(alex), [])
        self.assertEqual(alex.get(f"/api/friends/{sam_profile['id']}/plans").status_code, 404)
        self.assertEqual(self.going(sam), [])

        # Removing a plan removes the friend from "going".
        sam.put(f"/api/following/{alex_profile['id']}")
        self.assertEqual(self.going(alex), [sam_profile])
        sam.delete(f"/api/plans/{self.event}")
        self.assertEqual(self.going(alex), [])

    def test_unknown_event_is_404(self):
        alex, _ = self.account("alex")
        self.assertEqual(alex.get("/api/events/no-such-event/friends-going").status_code, 404)

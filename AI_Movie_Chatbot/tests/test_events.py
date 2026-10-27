"""Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v."""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app
from app.routes.events import start_time

EXPECTED_FIELDS = {"id", "title", "category", "date", "time", "location", "description"}


class EventsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_lists_six_sample_events(self):
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertEqual(len(events), 6)
        self.assertEqual(len({event["id"] for event in events}), 6)
        for event in events:
            with self.subTest(event=event["id"]):
                self.assertEqual(set(event), EXPECTED_FIELDS)

    def test_events_are_sorted_by_date_then_time_of_day(self):
        # The file lists 6:00 PM before 2:00 PM; the API must not depend on that.
        events = self.client.get("/api/events").json()
        self.assertEqual([event["id"] for event in events],
                         ["sample-2", "sample-1", "sample-4", "sample-3", "sample-6", "sample-5"])
        starts = [start_time(event) for event in events]
        self.assertEqual(starts, sorted(starts))

    def test_events_rejects_unsupported_method(self):
        self.assertEqual(self.client.post("/api/events").status_code, 405)


if __name__ == "__main__":
    unittest.main()

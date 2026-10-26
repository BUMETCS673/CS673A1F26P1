"""FV-118 HTTP demo works independently of event filtering or a catalog."""

import unittest

from fastapi.testclient import TestClient

from app.main import create_app


class ParserDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_category_only_returns_exact_parser_fields(self):
        response = self.client.post("/api/demo/parse-event-request", json={"message": "mUsIc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "category": "Music", "date": None, "needs_clarification": False,
        })

    def test_category_with_date(self):
        response = self.client.post("/api/demo/parse-event-request", json={"message": " Music on 2026-11-01 "})
        self.assertEqual(response.json(), {
            "category": "Music", "date": "2026-11-01", "needs_clarification": False,
        })

    def test_invalid_or_unsupported_text_requires_clarification(self):
        for message in ("", "music tomorrow", "music and food", "music on 2026-02-30", "movies"):
            with self.subTest(message=message):
                response = self.client.post("/api/demo/parse-event-request", json={"message": message})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {
                    "category": None, "date": None, "needs_clarification": True,
                })

    def test_invalid_payloads_are_rejected(self):
        for payload in ({}, {"message": 1}, {"message": "x" * 1001},
                        {"message": "music", "events": []}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/demo/parse-event-request", json=payload).status_code, 422)

    def test_no_filter_demo_is_registered(self):
        self.assertEqual(self.client.post("/api/demo/filter-events", json={}).status_code, 404)


if __name__ == "__main__":
    unittest.main()

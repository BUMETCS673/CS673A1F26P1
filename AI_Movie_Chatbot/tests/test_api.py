"""Run from AI_Movie_Chatbot: python -m unittest discover -s tests -v."""

import subprocess
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app, create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_health_contract(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.json(), {"status": "ok"})

    def test_existing_startup_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/plain"))
        self.assertEqual(response.text, "AI Movie Recommendation Chatbot is running")

    def test_unknown_route_returns_json_404(self):
        for path in ("/does-not-exist", "/api/does-not-exist"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": "Not Found"})

    def test_health_rejects_unsupported_method(self):
        self.assertEqual(self.client.post("/api/health").status_code, 405)

    def test_documentation_uses_reachable_schema(self):
        for path in ("/docs", "/redoc"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response.headers["content-type"])
                self.assertIn("/openapi.json", response.text)

    def test_openapi_describes_health_contract(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema["info"]["title"], "Event Planning API")
        health = schema["paths"]["/api/health"]["get"]
        self.assertEqual(health["tags"], ["health"])
        self.assertEqual(
            health["responses"]["200"]["content"]["application/json"]["schema"],
            {"$ref": "#/components/schemas/HealthResponse"},
        )
        self.assertIn("status", schema["components"]["schemas"]["HealthResponse"]["required"])

    def test_factory_creates_independent_apps(self):
        first, second = create_app(), create_app()
        self.assertIsNot(first, second)
        self.assertIsNot(app, first)
        first.add_api_route("/first-only", lambda: {"example": True})
        with TestClient(first) as first_client, TestClient(second) as second_client:
            self.assertEqual(first_client.get("/first-only").status_code, 200)
            self.assertEqual(second_client.get("/first-only").status_code, 404)

    def test_import_does_not_bind_a_socket_or_start_uvicorn(self):
        result = subprocess.run(
            [sys.executable, "-c", (
                "from unittest.mock import patch; "
                "import socket, uvicorn; "
                "guard = patch.object(socket.socket, 'bind', "
                "side_effect=AssertionError('import bound a socket')); "
                "guard.start(); "
                "server = patch.object(uvicorn, 'run', "
                "side_effect=AssertionError('import started uvicorn')); "
                "server.start(); "
                "from app.main import app, create_app; "
                "assert create_app() is not app"
            )],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

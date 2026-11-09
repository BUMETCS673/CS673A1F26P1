# AI-USAGE SUMMARY
# Authors: Yuchen Xu (feature requirements)
# Tools: OpenAI Codex
# Overall AI Contribution: Codex drafted this test.
# AI-Assisted Areas: Two-account API and persistence checks.
# Human Contributions: Yuchen Xu confirmed the one-way follow model.
# Notes/Verification: Run against a PostgreSQL database with migrations applied.

"""Exercise the follow endpoints with real sessions and PostgreSQL storage."""

import secrets
import unittest

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import create_app


class LiveFollowTests(unittest.TestCase):
    def signed_in_account(self):
        client = TestClient(create_app())
        self.addCleanup(client.close)
        username = f"follow_test_{secrets.token_hex(4)}"
        password = "live test password"
        response = client.post("/api/auth/register", json={
            "username": username,
            "display_name": username.title(),
            "email": f"{username}@example.com",
            "password": password,
            "activity_preferences": ["Music"],
        })
        self.assertEqual(response.status_code, 201, response.text)
        profile = {key: response.json()[key] for key in ("id", "username", "display_name")}
        self.addCleanup(self.delete_account, profile["id"])
        credentials = {"username": username, "password": password}
        self.assertEqual(client.post("/api/auth/login", json=credentials).status_code, 200)
        return client, profile, credentials

    def delete_account(self, user_id):
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = %s", (user_id,))

    def test_follow_requires_login(self):
        with TestClient(create_app()) as guest:
            for method, path in (
                ("GET", "/api/users/search?username=anybody"),
                ("GET", "/api/following"),
                ("GET", "/api/followers"),
                ("PUT", "/api/following/1"),
                ("DELETE", "/api/following/1"),
            ):
                with self.subTest(method=method, path=path):
                    self.assertEqual(guest.request(method, path).status_code, 401)

    def test_follow_is_one_way_persistent_and_owned_by_the_session(self):
        alice, alice_profile, alice_credentials = self.signed_in_account()
        bob, bob_profile, _ = self.signed_in_account()
        alice_path = f"/api/following/{alice_profile['id']}"
        bob_path = f"/api/following/{bob_profile['id']}"

        search = alice.get("/api/users/search", params={"username": bob_profile["username"].upper()})
        self.assertEqual(search.status_code, 200, search.text)
        self.assertEqual(search.json(), [bob_profile])
        unknown = alice.get("/api/users/search", params={"username": "no_such_account"})
        self.assertEqual(unknown.json(), [])
        self.assertEqual(alice.put(alice_path).status_code, 400)
        self.assertEqual(alice.put("/api/following/2147483647").status_code, 404)

        self.assertEqual(alice.put(bob_path).status_code, 204)
        self.assertEqual(alice.put(bob_path).status_code, 204)
        self.assertEqual(alice.get("/api/following").json(), [bob_profile])
        self.assertEqual(alice.get("/api/followers").json(), [])
        self.assertEqual(bob.get("/api/followers").json(), [alice_profile])
        self.assertEqual(bob.get("/api/following").json(), [])

        self.assertEqual(alice.post("/api/auth/logout").status_code, 204)
        self.assertEqual(alice.get("/api/following").status_code, 401)
        self.assertEqual(alice.post("/api/auth/login", json=alice_credentials).status_code, 200)
        self.assertEqual(alice.get("/api/following").json(), [bob_profile])

        # Bob cannot remove Alice's outgoing follow by supplying her account ID.
        spoofed_removal = bob.delete(bob_path, params={"follower_id": alice_profile["id"]})
        self.assertEqual(spoofed_removal.status_code, 204)
        self.assertEqual(bob.get("/api/followers").json(), [alice_profile])
        self.assertEqual(bob.put(alice_path).status_code, 204)
        self.assertEqual(alice.delete(bob_path).status_code, 204)
        self.assertEqual(alice.delete(bob_path).status_code, 204)
        self.assertEqual(alice.get("/api/following").json(), [])
        self.assertEqual(bob.get("/api/followers").json(), [])
        self.assertEqual(bob.get("/api/following").json(), [alice_profile])

# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: live HTTP stack checks
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: ran start_project.sh in WSL + Docker, checked localhost:3000, :8080/docs and /api/health/database

"""Live HTTP checks: python3 tests/check_stack.py [--expect-database-down]."""

import argparse
import json
import time
from urllib.error import HTTPError
from urllib.request import urlopen


def check(base_url: str, database_down: bool) -> None:
    cases = [
        ("/api/health", 200, {"status": "ok"}),
        ("/api/health/database", 503 if database_down else 200,
         {"detail": "Database unavailable. Check the backend configuration and database service."}
         if database_down else {"status": "ok", "database": "ok"}),
        ("/api/not-a-route", 404, {"detail": "Not Found"}),
    ]
    for path, expected_status, expected_body in cases:
        started = time.monotonic()
        try:
            response = urlopen(base_url.rstrip("/") + path, timeout=12)
        except HTTPError as error:
            response = error
        with response:
            assert response.status == expected_status, (path, response.status)
            assert response.headers.get_content_type() == "application/json", path
            assert json.load(response) == expected_body, path
        elapsed = time.monotonic() - started
        assert elapsed < 12, (path, elapsed)
        print(f"PASS {path}: HTTP {expected_status} ({elapsed:.3f}s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check the real Vite/API/database path.")
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--expect-database-down", action="store_true")
    args = parser.parse_args()
    check(args.base_url, args.expect_database_down)

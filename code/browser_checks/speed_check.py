# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)
# Update: OpenAI Codex, requested by Ji Wu: fail on request errors, incomplete
# workloads and individual three-second breaches; always clean up test accounts.
# Verification of this update: tests/test_speed_check.py (failure controls).

"""FV-109: chat response times with about 10 signed-in sessions at once, through the
website's /api proxy (localhost:3000) like a browser. Also times history and plans."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import secrets
import statistics
import sys
import threading
import time

import httpx2 as httpx

BASE = "http://localhost:3000"
ROUNDS = 20
MESSAGES = ["music this friday after 6pm", "food near the North End", "something fun tomorrow",
            "arts in Back Bay", "outdoors this weekend", "social after 7pm", "music near Fenway Park",
            "events today", "food on saturday", "asdf qwerty"]


def account(client, username):
    body = {"username": username, "display_name": "Speed", "email": f"{username}@example.com",
            "password": "speed test password", "activity_preferences": ["Music", "Food"]}
    for path, data, status in (("register", body, 201),
                               ("login", {"username": username, "password": body["password"]}, 200)):
        response = client.post(f"/api/auth/{path}", json=data)
        if response.status_code != status:
            raise RuntimeError(f"{path}: HTTP {response.status_code}")


def percentile(values, pct):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1)))]


def summary(label, values):
    if not values:
        return f"{label:32} n=   0  no samples"
    return (f"{label:32} n={len(values):4}  median={statistics.median(values):6.0f} ms  "
            f"p95={percentile(values, 95):6.0f} ms  max={max(values):6.0f} ms")


def workload(clients, rounds, *, clock=time.perf_counter):
    """Run every session concurrently and retain each failure and slow request.

    Workers return their own samples; future.result() propagates unexpected
    exceptions instead of allowing a crashed thread to look like a successful run.
    """
    barrier = threading.Barrier(len(clients), timeout=30)

    def session(index, client):
        samples, errors = [], []
        barrier.wait()
        for round_number in range(rounds):
            for path in ("chat", "history", "plans"):
                start = clock()
                status, failure = None, None
                try:
                    if path == "chat":
                        response = client.post("/api/chat", json={
                            "message": MESSAGES[(index + round_number) % len(MESSAGES)],
                        })
                    else:
                        response = client.get("/api/chat/history" if path == "history" else "/api/plans")
                    status = response.status_code
                except httpx.RequestError as error:
                    # Do not print response bodies, URLs, cookies or credentials.
                    failure = type(error).__name__
                sample = {"session": index, "round": round_number + 1, "path": path,
                          "ms": (clock() - start) * 1000, "status": status}
                samples.append(sample)
                if status != 200:
                    errors.append({**sample, "error": failure or f"HTTP {status}"})
        return samples, errors

    started = clock()
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        futures = [executor.submit(session, index, client) for index, client in enumerate(clients)]
        results = [future.result() for future in futures]
    return ([sample for samples, _ in results for sample in samples],
            [error for _, errors in results for error in errors], clock() - started)


def failures(samples, errors, sessions, rounds, max_chat_ms):
    """A successful exit requires a complete workload and no individual breach."""
    problems = list(errors)
    for path in ("chat", "history", "plans"):
        count = sum(sample["path"] == path for sample in samples)
        if count != sessions * rounds:
            problems.append({"path": path, "error": f"incomplete: {count}/{sessions * rounds}"})
    problems.extend({**sample, "error": f"exceeds {max_chat_ms:g} ms"}
                    for sample in samples if sample["path"] == "chat" and sample["ms"] > max_chat_ms)
    return problems


def cleanup_account(username):
    # Lazy import keeps the HTTP benchmark and its failure tests independent of Playwright.
    from common import sql
    sql(f"DELETE FROM users WHERE username = '{username}'")


def run(sessions, rounds, max_chat_ms=3000, *, client_factory=httpx.Client,
        cleanup=cleanup_account, benchmark=workload):
    clients, problems = [], []
    try:
        for _ in range(sessions):
            client = client_factory(base_url=BASE, timeout=30)
            username = f"speed_{secrets.token_hex(8)}"
            # Track before registration, so partial setup also gets cleaned up.
            clients.append((client, username))
            account(client, username)
        solo, solo_errors, _ = benchmark([clients[0][0]], rounds)
        samples, errors, wall = benchmark([client for client, _ in clients], rounds)
        problems.extend(failures(solo, solo_errors, 1, rounds, max_chat_ms))
        problems.extend(failures(samples, errors, sessions, rounds, max_chat_ms))
        print(f"HTTP-only; no model/provider; {sessions} sessions x {rounds} rounds, wall {wall:.1f} s")
        print(summary("POST /api/chat, 1 session alone", [s["ms"] for s in solo if s["path"] == "chat"]))
        for path in ("chat", "history", "plans"):
            print(summary(f"{path}, {sessions} at once", [s["ms"] for s in samples if s["path"] == path]))
        if wall > 0:
            print(f"requests/second overall: {len(samples) / wall:.0f}")
    except Exception as error:
        # Setup and worker failures are failures of the entire check, not missing samples.
        problems.append({"error": f"setup/workload failed: {type(error).__name__}"})
    finally:
        for client, username in clients:
            for action, function in (("close", client.close), ("cleanup", lambda: cleanup(username))):
                try:
                    function()
                except Exception as error:
                    problems.append({"error": f"{action} failed: {type(error).__name__}"})
    for problem in problems:
        print("FAIL:", problem)
    print("HTTP SPEED CHECK FAILED" if problems else "HTTP SPEED CHECK PASSED (browser rendering not measured)")
    return 1 if problems else 0


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="?", type=positive_int, default=10)
    parser.add_argument("--rounds", type=positive_int, default=ROUNDS)
    parser.add_argument("--max-chat-ms", type=positive_int, default=3000)
    args = parser.parse_args(argv)
    return run(args.sessions, args.rounds, args.max_chat_ms)


if __name__ == "__main__":
    sys.exit(main())

# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""FV-109: chat response times with about 10 signed-in sessions at once, through the
website's /api proxy (localhost:3000) like a browser. Also times history and plans."""

import secrets
import statistics
import sys
import threading
import time

import httpx

from common import sql

BASE = "http://localhost:3000"
SESSIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
ROUNDS = 20
MESSAGES = ["music this friday after 6pm", "food near the North End", "something fun tomorrow",
            "arts in Back Bay", "outdoors this weekend", "social after 7pm", "music near Fenway Park",
            "events today", "food on saturday", "asdf qwerty"]


def account():
    client = httpx.Client(base_url=BASE, timeout=30)
    username = f"speed_{secrets.token_hex(4)}"
    body = {"username": username, "display_name": "Speed", "email": f"{username}@example.com",
            "password": "speed test password", "activity_preferences": ["Music", "Food"]}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/login", json={"username": username, "password": body["password"]}).status_code == 200
    return client, username


def percentile(values, pct):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1)))]


def summary(label, values):
    return (f"{label:32} n={len(values):4}  median={statistics.median(values):6.0f} ms  "
            f"p95={percentile(values, 95):6.0f} ms  max={max(values):6.0f} ms")


clients = [account() for _ in range(SESSIONS)]
errors, chat_times, history_times, plan_times = [], [], [], []
lock = threading.Lock()

# Baseline: one session alone.
solo = []
for message in MESSAGES * 2:
    start = time.perf_counter()
    response = clients[0][0].post("/api/chat", json={"message": message})
    solo.append((time.perf_counter() - start) * 1000)
    assert response.status_code == 200, response.text

barrier = threading.Barrier(SESSIONS)


def session(index):
    client, _ = clients[index]
    barrier.wait()  # every session starts at the same moment
    for round_number in range(ROUNDS):
        for path, store in (("chat", chat_times), ("history", history_times), ("plans", plan_times)):
            start = time.perf_counter()
            if path == "chat":
                response = client.post("/api/chat", json={"message": MESSAGES[(index + round_number) % len(MESSAGES)]})
            elif path == "history":
                response = client.get("/api/chat/history")
            else:
                response = client.get("/api/plans")
            elapsed = (time.perf_counter() - start) * 1000
            with lock:
                store.append(elapsed)
                if response.status_code != 200:
                    errors.append((path, response.status_code, response.text[:100]))


threads = [threading.Thread(target=session, args=(i,)) for i in range(SESSIONS)]
wall = time.perf_counter()
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
wall = time.perf_counter() - wall

print(f"{SESSIONS} sessions x {ROUNDS} rounds (chat + history + plans), wall time {wall:.1f} s")
print(summary("POST /api/chat, 1 session alone", solo))
print(summary(f"POST /api/chat, {SESSIONS} at once", chat_times))
print(summary(f"GET /api/chat/history, {SESSIONS} at once", history_times))
print(summary(f"GET /api/plans, {SESSIONS} at once", plan_times))
print(f"requests/second overall: {(len(chat_times) + len(history_times) + len(plan_times)) / wall:.0f}")
print("errors:", errors or "none")
for client, username in clients:
    client.close()
    sql(f"DELETE FROM users WHERE username = '{username}'")

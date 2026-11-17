# Browser checks

Scripts that click through the running website in a real browser (Chromium, via
Playwright) the way a person would, with real accounts, the real API, and the
real database. They create their own test accounts and delete them at the end.
They are not part of the PR checks (those need no browser); run them before a
demo or after a big change.

**Setup (once):**

```bash
python -m pip install playwright httpx2
python -m playwright install chromium
```

**Run** with the project started (`./start_project.sh`), from this folder:

| Script | What it checks |
| --- | --- |
| `check_demo_story.py` | The whole Iteration 2 demo with two accounts: chat, Save, follow, "Alex is going", history after sign-in, Profile changing the chat order, phone size |
| `check_plans.py` | My Plans: save from cards (double click), details (keyboard), reload, remove, second account, phone/tablet/desktop |
| `check_friends.py` | Friends going with three accounts (mutual, one-way, unfollow) and the Friends page on a phone |
| `check_profile.py` | Profile edits, validation and focus, API rejects other fields, phone size |
| `check_xss.py` | FV-108: script-like text in every text input, then every place it is shown |
| `speed_check.py [sessions]` | FV-109: chat, history, and plans response times with N sessions at once (default 10) |

Each prints `ALL BROWSER CHECKS PASSED` (or the timings) and exits non-zero on a
problem, including console errors and 5xx responses. Screenshots go to `shots/`.

The speed check measures **HTTP response completion**, including session checks
and history writes, through the frontend proxy. It does not measure browser
rendering and cannot by itself establish FV-109's submission-to-usable-card target.
The current app uses a local fictional catalog and no model or external provider.

`python speed_check.py 10 --rounds 20 --max-chat-ms 3000` runs a single-session
baseline followed by 10 independent signed-in sessions. It prints median/p95/max
and every failed or over-limit request. Any non-200 response, transport error,
worker failure, incomplete workload, individual chat request above the threshold,
or cleanup failure exits with code 1. Setup failures also close clients and attempt
to remove every generated test account. The cleanup uses the project's local
Docker PostgreSQL instance, so run it only against the local disposable test stack.

Failure controls run in the normal Python unit-test job as
`tests/test_speed_check.py`; they simulate HTTP failures and are **not live latency
measurements**. Browser-render timings and the network/hardware configuration
still need to be recorded separately for the complete FV-109 acceptance criteria.

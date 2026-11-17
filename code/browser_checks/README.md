# Browser checks

Scripts that click through the running website in a real browser (Chromium, via
Playwright) the way a person would, with real accounts, the real API, and the
real database. They create their own test accounts and delete them at the end.
They are not part of the PR checks (those need no browser); run them before a
demo or after a big change.

**Setup (once):**

```bash
python -m pip install playwright httpx
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

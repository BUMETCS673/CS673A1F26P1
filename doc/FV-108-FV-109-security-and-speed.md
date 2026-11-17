# FV-108 Security Pass and FV-109 Chat Speed Check

**Date:** November 17, 2026 · **Tested by:** Daniel Winnie (taking over FV-108/FV-109 from the Iteration 2 plan), with Claude Code · **Build:** `main` after PRs #42–#45 (My Plans, friends going, Profile, chat wiring)

**Environment:** the project started with `./start_project.sh` (Docker: PostgreSQL 17, FastAPI on :8080, Vite on :3000) on WSL2, 16 CPU cores. Browser checks ran in headless Chromium through Playwright, against the real API and database, with throwaway test accounts deleted afterwards. The scripts are in `code/browser_checks/` so anyone can rerun them.

## Summary

| Area | Result |
| --- | --- |
| XSS in every text input (FV-108) | **Pass.** No script ran and no markup became page elements anywhere |
| Secrets in the frontend build (FV-108) | **Pass.** No passwords, database names, keys, or `VITE_` variables in `dist/` |
| Login required on every protected API route | **Pass.** 19 protected routes return 401 without a session |
| One account reading or changing another's data | **Pass.** Plans, follows, chat history, and profile are tied to the session only |
| Static analysis and dependency audits | **Pass.** Bandit 0 issues (939 lines); pip-audit and npm audit 0 known vulnerabilities |
| Chat speed with 10 sessions at once (FV-109) | **Pass.** `POST /api/chat` median 137 ms, p95 170 ms, max 187 ms, 0 errors |

## FV-108: Security pass

### Cross-site scripting (XSS)

`code/browser_checks/check_xss.py` typed these into every text input:

- `<img src=x onerror="window.__xss=1;alert(1)">`
- `<script>window.__xss=1</script>`
- `"><svg onload="window.__xss=1">`
- `javascript:window.__xss=1`
- `{{constructor.constructor('window.__xss=1')()}}`

| Input | Where the text is shown afterwards | Result |
| --- | --- | --- |
| Registration display name (two accounts) | Header "Signed in as", Friends search results and lists, "Alex is going", a friend's plans panel | Shown as plain text |
| Registration username | Rejected by the server (422): letters, numbers, `. _ -` only | Rejected |
| Chat request (all five, plus `music near <script>…`) | The chat conversation, then again after signing out and back in (saved history) | Shown as plain text |
| Friends search | The search results area | Shown as plain text |
| Profile display name (four payloads) | Header and Profile form | Shown as plain text |

The script fails on any alert dialog, the `window.__xss` flag being set, or an injected `<img>`, `<svg onload>`, or inline `<script>` element. A **negative control** (the same detector on a page that does use `innerHTML`) caught all three signals, so a clean result is meaningful.

Why it is safe: React escapes all text it renders, and the source has no `dangerouslySetInnerHTML`, `innerHTML`, `eval`, `new Function`, or `document.write` (searched with grep). The API returns JSON only. Unit tests also cover markup in event titles, display names, and event IDs.

### Secrets and configuration

- The production build (`npm run build`) was searched for the development database password and user, `DB_PASSWORD`, `POSTGRES_PASSWORD`, `password_hash`, private-key headers, and common API key formats (`sk-…`, `AKIA…`, `ghp_…`). **None found.** The frontend reads no environment variables, and Vite only passes `API_PROXY_*` to the dev proxy, never to the browser.
- Only `.env.example` files with placeholders are tracked in Git.
- Database errors return a generic 503 message. Tests confirm that driver messages, which can contain credentials, are never sent to the browser.

### Sessions and access control

- The session cookie is `HttpOnly`, `SameSite=Lax`, and limited to `/api`. JavaScript cannot read it (`document.cookie` checked in the browser). The database stores only a SHA-256 hash of each token. Logout deletes the session.
- **Route sweep:** every route in the API's OpenAPI list was called without a session. Public routes are health, register, login, and logout. All other 19 routes return **401**.
- **Ownership:** no request accepts a user ID for the signed-in user's own data, and every query filters by the session's user ID. Two- and three-account tests (unit, PostgreSQL, and in the browser) confirm all of the following:
  - One account cannot read or remove another's plans, follows, or chat history, including with a `user_id` query parameter.
  - `PATCH /api/auth/me` rejects `username`, `email`, `password`, and `id` (422) and changes only the session's account.
  - A friend's plans are visible only to **mutual** follows. One-way followers, unknown IDs, and yourself all get the same 404, so the endpoint does not reveal which accounts exist. Unfollowing removes access on the next request.
- SQL uses parameters everywhere. Bandit's only flags are the two reviewed `nosec` lines in `app/users.py` that insert a constant column list.

### Tools

| Tool | Scope | Result |
| --- | --- | --- |
| Bandit 1.9.4 | `code/AI_Movie_Chatbot/app` (939 lines) | 0 issues |
| pip-audit | `requirements.txt` | No known vulnerabilities |
| npm audit | `code/Web_Application` | 0 vulnerabilities |

### Known limitations (not fixed in Iteration 2)

- No rate limiting on login or registration, and no email verification.
- `SESSION_COOKIE_SECURE` is off by default because local development uses HTTP. Turn it on behind HTTPS.
- No Content-Security-Policy, X-Frame-Options, or X-Content-Type-Options headers (checked on :3000). React's escaping is the XSS defense today; a CSP would add a second layer for a real deployment.

## FV-109: Chat speed check

`code/browser_checks/speed_check.py` signs in N accounts. All sessions then start together, and each runs 20 rounds of `POST /api/chat` (ten different requests, including place and time constraints and one the parser cannot understand), `GET /api/chat/history`, and `GET /api/plans`. Requests go through the Vite proxy on :3000, as a browser does, and every exchange is saved to PostgreSQL.

| Load | Endpoint | Median | p95 | Max | Errors |
| --- | --- | --- | --- | --- | --- |
| 1 session | `POST /api/chat` | 40 ms | 45 ms | 47 ms | 0 |
| **10 sessions** | `POST /api/chat` | **137 ms** | **170 ms** | **187 ms** | **0** |
| 10 sessions | `GET /api/chat/history` | 135 ms | 161 ms | 181 ms | 0 |
| 10 sessions | `GET /api/plans` | 133 ms | 161 ms | 184 ms | 0 |
| 25 sessions | `POST /api/chat` | 328 ms | 394 ms | 544 ms | 0 |

There were about 75 requests per second in both runs (600 requests with 10 sessions, 1,500 with 25), and no request failed.

**Reading the numbers:** with 10 people at once, a chat answer takes well under a quarter of a second. Throughput stays at about 75 requests per second whether 10 or 25 sessions are active, so latency grows with load instead of failing. That pattern fits the development server running one worker process with auto-reload on. A deployment would run several workers (for example `uvicorn --workers 4`) to raise this ceiling. The demo catalog lives in memory, so the chat itself costs little; most of each request's time is the session check and the history write in PostgreSQL.

## Functional browser checks (for the STD)

These ran against the same build. All passed with no console errors and no 5xx responses.

| Script | Covers |
| --- | --- |
| `check_demo_story.py` | The full Iteration 2 demo with two accounts: chat ("food near the North End"), Save from the chat card, follow each other, "Alex is going", chat history with Save state after signing in again, Profile change reordering the chat (Music first, then Social first), honest no-match and clarification, phone (375 px) |
| `check_plans.py` | My Plans: a double click stores one row, Save by keyboard, reload, View details, Remove, second account sees nothing; 360 / 768 / 1280 px |
| `check_friends.py` | Three accounts: mutual follow, one-way follower never sees plans (UI and API), "Alex is going", unfollow removes access; phone layout |
| `check_profile.py` | Validation with focus, keyboard checkboxes, database row checked, API rejects username/email/ID, markup shown as text; phone layout |

On phone sizes, every check also verified that the page never scrolls sideways and that buttons are at least 44 px tall (FV-110 touch targets).

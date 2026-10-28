# Boston Events Planner (CS673 Team 1)

A web application that helps students, local residents, and tourists find
activities in Boston and nearby areas and make plans with friends. Users create
an account, browse upcoming events, filter them by category and date, and ask a
chat assistant for events in plain language. Later iterations add friends,
group chats, shared calendars, and notifications.

The project started as an "AI Movie Recommendation Chat Bot" (Iteration 0) and
changed direction to event planning at the 10/23 team meeting. Some folder and
database names, such as `AI_Movie_Chatbot/` and `movie_users`, keep the old
name so existing setups keep working.

| Folder | Iteration 1 deliverable |
| --- | --- |
| [`code/`](code/) | Runnable source code and tests |
| [`doc/`](doc/) | Presentation, SPPP, risk management, SDD, STD, progress report, meeting minutes |
| [`demo/`](demo/) | Iteration demo video |
| `README.md` | This file |

## Status: Iteration 1

| Works now | Planned next (Iteration 2+) |
| --- | --- |
| Register with a display name, email, password, and activity preferences; log in and log out (scrypt password hashes, server-side sessions, HttpOnly cookie) | Friends, private and group chat |
| Event feed of six fictional Boston sample events, served by the Python API and ordered by date and time | Personal and group calendars, custom events |
| Category and date filters | A real Boston event data source |
| Chat panel: rule-based request parser (`Music on 2026-11-01`) and filter demo, no AI key needed | An AI service for natural-language recommendations |
| Swagger API docs, database health check, one-command Docker startup | Notifications, online deployment |

Everything runs locally in Docker; nothing is deployed online yet.

## Quick start

Requires Docker Desktop (on Windows, use an Ubuntu/WSL terminal). From the
repository root:

```bash
cd code
./start_project.sh
```

When it prints **"The project is ready!"**, open:

| Address | What it is |
| --- | --- |
| http://localhost:3000 | The web app: register, log in, browse, filter, chat |
| http://localhost:8080/docs | Interactive API documentation (Swagger UI) |
| http://localhost:3000/api/health/database | Checks the React → Python → PostgreSQL chain |

Full setup, troubleshooting, and the destructive cleanup script
(`code/stop_project.sh` deletes the local database) are in
**[code/HOW_TO_START_AND_STOP_PROJECT.md](code/HOW_TO_START_AND_STOP_PROJECT.md)**.

## Architecture

```
Browser ──► React 19 + Vite (:3000) ──/api──► FastAPI + Uvicorn (Python 3.12) ──► PostgreSQL 17
                                     nginx (:8080) ──┘
```

All three parts run as Docker Compose services on one network. The browser
never sees database credentials or API keys; only the Python server talks to
the database. The design is described in the SDD (see Documents).

## Repository layout

| Folder | Contents |
| --- | --- |
| [`code/Web_Application/`](code/Web_Application/README.md) | React frontend: `src/App.jsx`, components (event feed, filters, chat panel, login/registration forms), form preview pages |
| [`code/AI_Movie_Chatbot/`](code/AI_Movie_Chatbot/README.md) | Python FastAPI backend: `app/routes/` (health, events, auth, demo parser/filter), `app/users.py` and `app/passwords.py` (accounts), `app/data/sample_events.json`, nginx config, and `tests/` |
| [`code/User_Database/`](code/User_Database/README.md) | PostgreSQL service: `init.sql` and versioned `migrations/` |
| `code/start_project.sh`, `code/stop_project.sh` | Start everything with one command; remove everything (including data) |
| [`doc/`](doc/) | Iteration documents; Iteration 0's submission is in [`doc/iteration0/`](doc/iteration0/) |
| `demo/`, `misc/` | Demo videos; other material |

## Tests

From `code/AI_Movie_Chatbot/`, with Python 3.12 and `requirements-dev.txt` installed:

```bash
python -m unittest discover -s tests -v                        # 65 unit tests, no database needed
python -m unittest discover -s tests -p "live_*.py" -v          # live checks against the running PostgreSQL
```

Static analysis: `bandit -r code/AI_Movie_Chatbot/app` reports no open findings.

## Development process

- **Branches:** one feature branch per Jira task (for example `feature/FV-117-event-filters`), merged into `main` through a pull request.
- **Tracking:** user stories, tasks, and sprints are in Jira ([FV project](https://f26a1team1.atlassian.net/browse/FV)). Defects go in GitHub Issues.
- **Releases:** each iteration ends with a GitHub release containing the code and the iteration's documents.
- **AI usage:** the course requires four layers of AI logging:
  1. the AIUsageLog sheet in the progress report
  2. an AI table in every document
  3. `[AI]` / `[HUMAN]` / `[HYBRID]` commit tags
  4. an `AI-USAGE SUMMARY` header at the top of every source file

## Documents

Team documents are written in the team Google Drive and exported to
[`doc/`](doc/) for each release (see [`doc/Readme.md`](doc/Readme.md) for the file list):

- SPPP: project proposal and plan, with the risk management sheet
- SDD: software design document
- STD: software test document
- Meeting minutes and the progress report (weekly reports and AI usage log)
- Iteration presentations

## Team

| Member | Role |
| --- | --- |
| Junshuo Huang | Team Leader |
| Yung Cheng (Ryan) Chiu | Requirements Leader |
| Daniel Winnie | Design and Implementation Leader |
| Yuchen Xu | Configuration Leader |
| Jibek Kelgenbaeva | QA Leader |
| Ji Wu | Security Leader |

Introductions are in [team.md](team.md).

<!-- AI-USAGE: README rewritten with Claude Code (Claude Opus) from the repository, SPPP, and Jira; facts checked against the code and test run by Daniel Winnie. -->

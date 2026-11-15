This folder contains all source code and test code.

| Path | Contents |
| --- | --- |
| [`Web_Application/`](Web_Application/README.md) | React + Vite frontend |
| [`AI_Movie_Chatbot/`](AI_Movie_Chatbot/README.md) | Python FastAPI backend and its tests (`tests/`) |
| [`User_Database/`](User_Database/README.md) | PostgreSQL setup: `init.sql` and `migrations/` |
| `start_project.sh` / `stop_project.sh` | Start the whole stack in Docker / remove it, including local data |
| [`HOW_TO_START_AND_STOP_PROJECT.md`](HOW_TO_START_AND_STOP_PROJECT.md) | Full setup, run, and troubleshooting guide |

Run from this folder: `./start_project.sh`, then open http://localhost:3000.

## Automatic PR checks

Every pull request to `main` (and every push to `main`) runs
[`.github/workflows/pr-checks.yml`](../.github/workflows/pr-checks.yml) on GitHub:

| Job | What it runs |
| --- | --- |
| Python unit tests | `python -m unittest discover -s tests -v` in `AI_Movie_Chatbot` (no database) |
| Python live database tests | `init.sql` and every migration on a fresh PostgreSQL 17, then all `tests/live_*.py` |
| Frontend tests and build | `npm ci`, `npm test`, and `npm run build` in `Web_Application` |

**If a check fails:** on the PR page, click **Details** next to the red X, open the
failing step, and scroll to the first error. Run the same command locally from the
folder shown above, fix it, and push again; the checks rerun automatically. To rerun
without a new commit (for example after a network hiccup), open the run in the
**Actions** tab and choose **Re-run failed jobs**. A new migration must be safe to run
after `init.sql` (use `IF NOT EXISTS`), because the live job applies both.

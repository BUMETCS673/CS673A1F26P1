This folder contains all source code and test code.

| Path | Contents |
| --- | --- |
| [`Web_Application/`](Web_Application/README.md) | React + Vite frontend |
| [`AI_Movie_Chatbot/`](AI_Movie_Chatbot/README.md) | Python FastAPI backend and its tests (`tests/`) |
| [`User_Database/`](User_Database/README.md) | PostgreSQL setup: `init.sql` and `migrations/` |
| `start_project.sh` / `stop_project.sh` | Start the whole stack in Docker / remove it, including local data |
| [`HOW_TO_START_AND_STOP_PROJECT.md`](HOW_TO_START_AND_STOP_PROJECT.md) | Full setup, run, and troubleshooting guide |

Run from this folder: `./start_project.sh`, then open http://localhost:3000.

## Adding a feature

| You need to... | Do this |
| --- | --- |
| Add API routes | Create a new file in `AI_Movie_Chatbot/app/routes/`, then add it to the router list in `app/main.py`. |
| Require a logged-in user | Add `user: dict = Depends(require_user)` to the route (see `require_user` in `app/routes/auth.py`). It returns 401 when there is no valid session. |
| Change the database | Add a new numbered file in `User_Database/migrations/` (the next unused number, e.g. `003_...sql`) using `IF NOT EXISTS`. `start_project.sh` applies it; editing `init.sql` is not required. |
| Call the API from React | Add a function under your feature's section in `Web_Application/src/api.js`. |

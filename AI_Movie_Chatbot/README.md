# Python API foundation

The backend uses Python 3.12, FastAPI for routes and request/response schemas,
and Uvicorn to run the application. nginx forwards local port 8080 to Uvicorn
on container port 8000. The folder keeps its historical movie-chatbot name;
new feature work targets event planning.

## Run with Docker

From the repository root:

```bash
bash start_project.sh
```

This starts PostgreSQL first, which creates the shared `cs673_event_planning`
network, then the backend and frontend. It preserves existing database data.
Docker installs the Python dependencies; no local Python installation is needed.
For backend-only work, start the database before the backend:

```bash
docker compose --project-directory User_Database up -d --wait
docker compose --project-directory AI_Movie_Chatbot up -d --build --wait --wait-timeout 120
```

| URL | Response |
| --- | --- |
| http://localhost:8080/ | Original plain-text startup message |
| http://localhost:8080/api/health | HTTP 200 with `{"status":"ok"}` |
| http://localhost:3000/api/health/database | Vite → Python → PostgreSQL; HTTP 200 with `{"status":"ok","database":"ok"}` |
| http://localhost:8080/docs | Interactive Swagger API documentation |
| http://localhost:8080/redoc | Alternative API reference |
| http://localhost:8080/openapi.json | Generated OpenAPI schema |
| http://localhost:8080/does-not-exist | HTTP 404 with `{"detail":"Not Found"}` |

`/api/health` measures API liveness only. `/api/health/database` runs `SELECT 1`
using the reusable PostgreSQL helper; it returns HTTP 503 with a generic useful
message when configuration or the database is unavailable. It reads no user
records and returns no connection settings. Both endpoints also work through
nginx on port 8080. The interactive docs can call them through nginx.

The Docker development server reloads automatically after saving Python or JSON
files under `app/`. Keep the project running; refresh your browser or repeat
the API request to see the changed response. New files under `app/` are shared
with the container too. Source is mounted read-only; edit it on your computer.
Polling supports saves from Windows/WSL editors. Uvicorn's reload mode is enabled
by Compose for development; the Dockerfile's standalone command is unchanged.

After requirements, Docker, or environment changes, rerun `./start_project.sh`
to rebuild/recreate the apps. Database changes still need migrations. Inspect
reload/startup errors with:

```bash
docker compose --project-directory AI_Movie_Chatbot logs app web
```

Stop just the backend containers and network with:

```bash
docker compose --project-directory AI_Movie_Chatbot down
```

## Optional local Python workflow

From `AI_Movie_Chatbot`, with Python 3.12 installed:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Match the default local Docker database. These are dummy development credentials.
export DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=movie_users DB_USER=movie_admin
export DB_PASSWORD=local_dev_password
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start PostgreSQL with the database-only Docker command above before using its
diagnostic endpoint. For Windows PowerShell, use `py -3.12 -m venv .venv`, activate
with `.venv\Scripts\Activate.ps1`, and set each variable with, for example,
`$env:DB_HOST = "127.0.0.1"`. Open http://localhost:8000/docs for this workflow.
Press Ctrl+C to stop. Run module commands from `AI_Movie_Chatbot` so Python can
find the `app` package.

## Where to add a feature

### Independent FV-117 browser demo

Start the stack with `bash start_project.sh` and open http://localhost:3000.
After the fake demo login, enter JSON in the chat panel's **Filter conditions
(JSON)** input and click **Filter sample events**:

- `{"category":"Music"}` returns two samples.
- `{"category":"Music","date":"2026-11-01"}` returns one.
- `{"date":"2026-11-01"}` returns the two samples on that date.
- `{}` returns all six; `{"category":"Music","date":"2026-11-02"}` returns none.

`POST /api/demo/filter-events` takes optional `category` and `date`, plus the
browser's full existing fictional `events` list, and calls `filter_events`.
The list is client-supplied demo data, not an authoritative catalog. No login,
database, external model, or FV-118 parser is introduced. Natural-language text
is deliberately not accepted in this branch. This is not complete FV-99.

- `app/main.py`: `create_app()` creates FastAPI and registers feature routers.
  The exported `app` is Uvicorn's entry point. Importing it does not run a server.
- `app/routes/health.py`: a complete small route with a typed JSON response.
- `app/database.py`: reads server environment settings and opens one connection
  per operation. Its context manager commits on success, rolls back on error,
  and always closes the connection. Sync routes using it should use `def` so
  FastAPI runs blocking database work in its thread pool.
- `tests/test_api.py`: checks the API contract, docs, factory, and import safety.

For a new feature, create a module under `app/routes/` using `APIRouter`, define
its request/response models, and register the router inside `create_app()`.
For example, an events router with `@router.get("/events")`, registered using
`application.include_router(events.router, prefix="/api", tags=["events"])`,
serves `/api/events`. Add tests for the feature's behavior and failure cases.
Routes appear automatically in `/docs` and `/openapi.json`.

For database access inside a synchronous route or service:

```python
from app.database import get_connection

with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
```

Pass user values as query parameters, as above. Feature owners add their own
authorization and schemas. Do not log the connection options or driver exception
messages: they can contain credentials.

## Server configuration

The default Docker setup supplies dummy local settings matching `User_Database`;
no `.env` is needed. For another existing database, copy `.env.example` to `.env`
inside `AI_Movie_Chatbot`, replace every placeholder, and rebuild/recreate the
backend. Compose loads this folder's `.env`; exported shell variables take
precedence. Those overrides configure the API connection, not PostgreSQL's
initialization or its existing accounts. Avoid a separate root `.env` so Compose
does not pick up competing settings.

| Variable | Purpose |
| --- | --- |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Required by the Python helper; Docker supplies defaults |
| `DB_PORT` | Defaults to 5432; valid range 1–65535 |
| `DB_CONNECT_TIMEOUT` | Connection timeout in seconds, 2–5; defaults to 3 |
| `DB_STATEMENT_TIMEOUT_MS` | PostgreSQL query timeout in milliseconds, 1–5000; defaults to 2000 |

Use `database` inside Docker and `127.0.0.1` for a native Python server talking
to the local published database port. A single host is supported. Connection
timeouts apply to connection attempts; hostname resolution also depends on the
local DNS service. The default Docker service name resolves on its shared network.
Missing/invalid settings produce a safe diagnostic 503, while liveness and docs
remain usable. Native Python reads exported environment variables; it does not
automatically load `.env`. Git and Docker ignore secret-bearing `.env` files.

## Run checks

With the local virtual environment activated, from `AI_Movie_Chatbot`:

```bash
python -m pip install -r requirements-dev.txt
python -m pip check
python -m unittest discover -s tests -v
```

Tests use FastAPI's TestClient and Python's built-in unittest runner. They need
neither a running server nor PostgreSQL. With the local database environment
variables above configured and PostgreSQL running, also run the explicit live
connection/cleanup/timeout tests:

```bash
python -m unittest discover -s tests -p live_database.py -v
```

These verify connection cleanup after success and failure, a real query timeout,
and a bounded connection attempt to a deliberately unresponsive local server.
Also check the real Docker/nginx path
after changing startup or proxy configuration. From the repository root:

```bash
bash start_project.sh
docker compose --project-directory AI_Movie_Chatbot ps
curl --fail http://localhost:8080/api/health
curl --fail http://localhost:8080/docs
curl --fail http://localhost:8080/openapi.json
curl --fail http://localhost:3000/api/health/database
curl -i http://localhost:8080/does-not-exist
```

Expect healthy `app` and `web` containers, HTTP 200 for health/docs/schema,
and HTTP 404 for the last request. For a live outage check, stop PostgreSQL,
expect a safe 503 at the frontend diagnostic URL and 200 at `/api/health`, then
start PostgreSQL and confirm recovery:

```bash
docker compose --project-directory User_Database stop database
curl -i http://localhost:3000/api/health/database
curl --fail http://localhost:3000/api/health
docker compose --project-directory User_Database start database
```

For repeatable HTTP assertions with Python 3's standard library, run from the
repository root after startup:

```bash
python3 AI_Movie_Chatbot/tests/check_stack.py
```

While the database is stopped, add `--expect-database-down`. For a local Vite
server, add `--base-url http://localhost:5173`. These checks cover JSON success,
safe database failure, liveness, and proxy forwarding of unknown API routes.

Stopping/starting the database preserves its volume. The separate root
`stop_project.sh` deliberately deletes local data. Shut down frontend and backend
before taking the database Compose project down, because they use its network.

## Dependency versions

`requirements.txt` pins both runtime packages and their resolved dependencies.
`requirements-dev.txt` adds the pinned HTTP test client and its extra dependencies.
The production image installs only `requirements.txt`.

To update dependencies, use a fresh Python 3.12 virtual environment, install the
chosen FastAPI/Uvicorn/psycopg[binary]/watchfiles versions, and run `python -m pip freeze` to regenerate the
runtime pins. Install the chosen httpx2 version afterward and update only the
extra test pins in `requirements-dev.txt`. Run `pip check`, the tests, and the
Docker checks before committing the updated versions.

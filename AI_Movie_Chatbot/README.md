# Python API foundation

The backend uses Python 3.12, FastAPI for routes and request/response schemas,
and Uvicorn to run the application. nginx forwards local port 8080 to Uvicorn
on container port 8000. The folder keeps its historical movie-chatbot name;
new feature work targets event planning.

## Run with Docker

From the repository root:

```bash
docker compose --project-directory AI_Movie_Chatbot up -d --build --wait --wait-timeout 120
```

Or use `bash start_project.sh` to start the frontend and database as well.
Docker installs the Python dependencies; no local Python installation is needed.

| URL | Response |
| --- | --- |
| http://localhost:8080/ | Original plain-text startup message |
| http://localhost:8080/api/health | HTTP 200 with `{"status":"ok"}` |
| http://localhost:8080/docs | Interactive Swagger API documentation |
| http://localhost:8080/redoc | Alternative API reference |
| http://localhost:8080/openapi.json | Generated OpenAPI schema |
| http://localhost:8080/does-not-exist | HTTP 404 with `{"detail":"Not Found"}` |

The health endpoint measures API liveness only. Database connectivity, frontend
API integration, authentication, and event features are separate work items.
The interactive docs can call the implemented health endpoint through nginx.

After source changes, repeat the startup command to rebuild the image. Inspect
startup errors with:

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
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

For Windows PowerShell, use `py -3.12 -m venv .venv` and activate with
`.venv\Scripts\Activate.ps1`. Open http://localhost:8000/docs for this workflow.
Press Ctrl+C to stop. Run module commands from `AI_Movie_Chatbot` so Python can
find the `app` package.

## Where to add a feature

- `app/main.py`: `create_app()` creates FastAPI and registers feature routers.
  The exported `app` is Uvicorn's entry point. Importing it does not run a server.
- `app/routes/health.py`: a complete small route with a typed JSON response.
- `tests/test_api.py`: checks the API contract, docs, factory, and import safety.

For a new feature, create a module under `app/routes/` using `APIRouter`, define
its request/response models, and register the router inside `create_app()`.
For example, an events router with `@router.get("/events")`, registered using
`application.include_router(events.router, prefix="/api", tags=["events"])`,
serves `/api/events`. Add tests for the feature's behavior and failure cases.
Routes appear automatically in `/docs` and `/openapi.json`.

## Run checks

With the local virtual environment activated, from `AI_Movie_Chatbot`:

```bash
python -m pip install -r requirements-dev.txt
python -m pip check
python -m unittest discover -s tests -v
```

Tests use FastAPI's TestClient and Python's built-in unittest runner. They need
neither a running server nor PostgreSQL. Also check the real Docker/nginx path
after changing startup or proxy configuration. From the repository root:

```bash
docker compose --project-directory AI_Movie_Chatbot up -d --build --wait --wait-timeout 120
docker compose --project-directory AI_Movie_Chatbot ps
curl --fail http://localhost:8080/api/health
curl --fail http://localhost:8080/docs
curl --fail http://localhost:8080/openapi.json
curl -i http://localhost:8080/does-not-exist
```

Expect healthy `app` and `web` containers, HTTP 200 for health/docs/schema,
and HTTP 404 for the last request.

## Dependency versions

`requirements.txt` pins both runtime packages and their resolved dependencies.
`requirements-dev.txt` adds the pinned HTTP test client and its extra dependencies.
The production image installs only `requirements.txt`.

To update dependencies, use a fresh Python 3.12 virtual environment, install the
chosen FastAPI/Uvicorn versions, and run `python -m pip freeze` to regenerate the
runtime pins. Install the chosen httpx2 version afterward and update only the
extra test pins in `requirements-dev.txt`. Run `pip check`, the tests, and the
Docker checks before committing the updated versions.

# HOW TO START AND STOP THE PROJECT

**Start everything: `./start_project.sh`**

**Remove everything: `bash stop_project.sh`**

Run these commands in a terminal opened in the repository's root folder (the
folder containing this file). You do not need to start each app separately.

## Set up your computer once

1. Install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/).
   It includes Docker Compose. Linux users can instead use Docker Engine with
   the Compose plugin. Use a version supporting `docker compose up --wait`.
   In Docker Desktop, turn on **Settings > General > Start Docker Desktop when
   you sign in to your computer** so the project comes back after a reboot.
2. On Windows, use an Ubuntu/WSL terminal and enable that distribution under
   Docker Desktop's **Settings > Resources > WSL Integration**. On macOS or
   Linux, use your normal Bash-capable terminal.
3. Clone this repository's `main` branch with Git, or download and extract its ZIP from
   GitHub. Open the project folder in your editor and open its terminal.

**You do not need to install Node.js, npm, Python, PostgreSQL, or nginx locally
for these scripts.** Docker supplies them, including running `npm ci` for you.
Local Node.js and npm are only needed for the optional frontend-only workflow
in `Web_Application/README.md`.

Keep Docker running. The first start needs an internet connection to download
images and Python/npm packages. Ports **3000**, **8080**, and **5432** must be free.

## Start the whole project

```bash
./start_project.sh
```

Wait for **"The project is ready!"** The first start may take a few minutes.
Docker builds the app images, creates the containers, and checks that all three
parts respond. You can close the terminal afterward; the containers keep running.

| Part | Address | What it does right now |
| --- | --- | --- |
| React website | **http://localhost:3000** | Boston events prototype. **Register** a new account or **Log in** with an existing one; accounts are checked by the Python API and saved in PostgreSQL. Fictional event cards are served by the API, soonest first. |
| Python API | **http://localhost:8080/docs** | FastAPI documentation: health checks, `/api/auth/*` (register, login, me, logout), `/api/events`, and the chat demos. Recommendations are future work. |
| PostgreSQL user database | **localhost:5432** | Stores registered accounts (hashed passwords) and login sessions, plus two sample users who have no password; this is a database connection, not a browser page. |

For either website address, right-click the address in your terminal to open it
(if your terminal supports that), or copy and paste it into your browser's
address bar. These addresses are for your own computer.

The development services are connected. Open
**http://localhost:3000/api/health/database** to send a request through Vite and
Python to PostgreSQL. Expect `{"status":"ok","database":"ok"}`; this checks
`SELECT 1` and returns no user records. The chat actions call the Python demo
endpoints; they do not save messages. Backend
development and test instructions are in [AI_Movie_Chatbot/README.md](AI_Movie_Chatbot/README.md).

To view the database, open a second terminal in the repository root and run:

```bash
docker compose --project-directory User_Database exec database psql -U movie_admin -d movie_users
```

At the database prompt, type the following, including the semicolon:

```sql
SELECT * FROM users;
```

Type `\q` and press Enter to return to your normal terminal. For a graphical
database client, use host `localhost`, port `5432`, database `movie_users`,
username `movie_admin`, and password `local_dev_password` (local development
only). More SQL examples are in `User_Database/README.md`.

## Edit while the project is running

Leave the containers running and save your files:

| What you changed | What happens / what to do |
| --- | --- |
| React components, CSS, HTML, or frontend sample data | Vite updates/reloads the open browser automatically. |
| Python files under `AI_Movie_Chatbot/app` | The API server reloads automatically. Refresh the page or repeat the request to see the new response. |
| JSON files under `AI_Movie_Chatbot/app` | The API server reloads automatically so cached sample data can be loaded again. |
| npm/Python dependencies, Dockerfiles, Compose settings, or environment configuration | Run `./start_project.sh` again to rebuild/recreate the apps. No stop command is needed. |
| Database SQL/schema | Apply the appropriate migration explicitly. Saving `init.sql` does not modify an existing database. |
| You ran `git pull` or switched branches | Run `./start_project.sh` once. It is always safe, keeps database data, and picks up any new dependencies a teammate added. |

### After a reboot or closing Docker Desktop

You do not need to run anything. Once Docker Desktop is open again, all
containers start by themselves (give them about a minute). To make this fully
automatic after restarting your computer, turn on Docker Desktop's
**Settings > General > Start Docker Desktop when you sign in to your computer**.

Logins are real server sessions stored in an HttpOnly cookie, so reloading the
page keeps you logged in for up to 7 days. **Log Out** ends the session and shows
the login pop-up again. Each start also applies `User_Database/migrations/*.sql`;
they are safe to repeat, so an older local database gains the account columns
and the `user_sessions` table without losing data.

Docker sees the live source files and polls for changes to support Windows/WSL
editors too. Frontend dependencies and Vite's cache live in a Docker volume,
separate from host `node_modules`. The startup script refreshes that dependency
volume from the rebuilt image, and keeps the PostgreSQL data volume. On a fresh
checkout it creates an empty host `node_modules` directory as the mount point;
you still do not need npm or a local package installation.

The frontend project and Python app are mounted read-only inside containers;
edit them in your normal host editor. For a production-build check inside the
frontend container, use a writable output directory:

```bash
docker compose --project-directory Web_Application exec website npm run build -- --outDir /tmp/frontend-build
```

PostgreSQL owns the shared `cs673_event_planning` network. The startup script
starts it before the apps; the stop script removes the apps before the database.
No local environment file is required for the dummy development database.
Optional server configuration is documented in `AI_Movie_Chatbot/README.md`;
keep credentials out of React and browser environment variables.

## Finish and delete the local project containers

```bash
bash stop_project.sh
```

**This deletes all project containers, their networks, locally built app images,
and the database volume, including ALL users and changes you added locally.**
It does not ask for confirmation. Source files and other Docker projects are
kept. Shared downloaded images such as PostgreSQL, Python, Node, and nginx may
remain cached so the next setup is faster. Host `node_modules` and `dist`
folders, if you created them separately, are left alone.

The next `bash start_project.sh` rebuilds the apps and creates a fresh database
from `User_Database/init.sql`, with the original two sample users. The stop
script also works after a partial startup and can be run more than once.

## If something fails

- **Docker is missing or not running:** install/start Docker Desktop and check
  WSL integration on Windows. Confirm `docker info` works in your terminal.
- **`--wait` is not recognized:** update Docker Desktop or your Compose plugin.
- **A port is already in use:** close the other program using the port. If an
  earlier project run is still present, rerun `./start_project.sh`; it manages
  this project's containers without deleting database data.
- **Build or startup failed:** read the error above the script's explanation.
  Check your internet connection and Docker's available disk space. Fix the
  cause and run `./start_project.sh` again; cleanup is not required for a rebuild.
- **Saved changes do not appear:** wait a moment, then inspect the frontend/API
  logs for compilation/import errors. Fix the error and save again. Verify you
  are editing this checkout and viewing http://localhost:3000, not an old preview.
- **Need container logs?** For example, run
  `docker compose --project-directory AI_Movie_Chatbot logs`. Replace the folder
  with `Web_Application` or `User_Database` for the other parts.

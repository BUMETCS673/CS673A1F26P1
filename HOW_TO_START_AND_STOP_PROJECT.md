# HOW TO START AND STOP THE PROJECT

**Start everything: `bash start_project.sh`**

**Remove everything: `bash stop_project.sh`**

Run these commands in a terminal opened in the repository's root folder (the
folder containing this file). You do not need to start each app separately.

## Set up your computer once

1. Install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/).
   It includes Docker Compose. Linux users can instead use Docker Engine with
   the Compose plugin. Use a version supporting `docker compose up --wait`.
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
bash start_project.sh
```

Wait for **"The project is ready!"** The first start may take a few minutes.
Docker builds the app images, creates the containers, and checks that all three
parts respond. You can close the terminal afterward; the containers keep running.

| Part | Address | What it does right now |
| --- | --- | --- |
| React website | **http://localhost:3000** | Boston events scaffold with an explicitly fake login, fictional event cards, sample filters, and preset chat replies. |
| Python API | **http://localhost:8080/docs** | FastAPI documentation with a working `/api/health` endpoint. The original status page remains at `/`; recommendations are future work. |
| PostgreSQL user database | **localhost:5432** | Stores the two sample users; this is a database connection, not a browser page. |

For either website address, right-click the address in your terminal to open it
(if your terminal supports that), or copy and paste it into your browser's
address bar. These addresses are for your own computer.

The development services are connected. Open
**http://localhost:3000/api/health/database** to send a request through Vite and
Python to PostgreSQL. Expect `{"status":"ok","database":"ok"}`; this checks
`SELECT 1` and returns no user records. The chat form still uses sample replies.
Sending a chat message does not yet contact the backend or save it. Backend
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

After editing app code, run `bash start_project.sh` again. It rebuilds the images
and replaces the containers. It keeps existing database data until you use the
stop script. There is no automatic source-code reload in this Docker workflow.

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
  earlier project run is still present, run `bash stop_project.sh` first.
- **Build or startup failed:** read the error above the script's explanation.
  Check your internet connection and Docker's available disk space. Run
  `bash stop_project.sh`, fix the cause, and run `bash start_project.sh` again.
- **Need container logs?** For example, run
  `docker compose --project-directory AI_Movie_Chatbot logs`. Replace the folder
  with `Web_Application` or `User_Database` for the other parts.

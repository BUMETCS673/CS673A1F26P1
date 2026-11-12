#!/usr/bin/env bash
# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (migrations on start)
# Overall AI Contribution: ~90%
# AI-Assisted Areas: one-command startup, health waits, migrations
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: ran start_project.sh in WSL + Docker, checked localhost:3000, :8080/docs and /api/health/database

# Start all three parts from any working directory. Bash stops on errors.
set -euo pipefail

# Find this script's folder instead of assuming where the terminal was opened.
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is missing. Install and start Docker Desktop first."
  echo "See HOW_TO_START_AND_STOP_PROJECT.md for setup instructions."
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose is missing. Install or update Docker Desktop."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Cannot connect to Docker. Start Docker Desktop and try again."
  echo "On Windows, also enable Docker Desktop's WSL integration."
  exit 1
fi

# Keep errors visible; retrying startup does not require deleting database data.
trap 'echo "Startup did not finish. Read the error above, fix it, and rerun ./start_project.sh. Existing database data is kept."' ERR

echo "Starting the project. The first run downloads images and may take a few minutes."
echo "You do not need to install npm packages yourself."

# Each folder keeps its own Compose setup. --wait waits for healthy services.
# Rebuild app dependencies on startup. Normal source edits reload while running.
echo "[1/3] Starting PostgreSQL and creating sample users if the database is empty..."
docker compose --project-directory "$PROJECT_ROOT/User_Database" up -d --wait --wait-timeout 120

# init.sql only runs for an empty volume. Migrations bring an existing database
# up to date; each one uses IF NOT EXISTS, so applying them again is harmless.
echo "      Applying database migrations (safe to repeat)..."
for migration in "$PROJECT_ROOT"/User_Database/migrations/*.sql; do
  docker compose --project-directory "$PROJECT_ROOT/User_Database" exec -T database \
    psql -q -v ON_ERROR_STOP=1 -U movie_admin -d movie_users < "$migration"
done

echo "[2/3] Building and starting the FastAPI backend..."
docker compose --project-directory "$PROJECT_ROOT/AI_Movie_Chatbot" up -d --build --force-recreate --wait --wait-timeout 120

echo "[3/3] Installing React dependencies inside Docker and starting the website..."
# A read-only project mount needs this empty mount point to exist on a fresh
# checkout. Create it as the host user; actual packages live in Docker's volume.
mkdir -p "$PROJECT_ROOT/Web_Application/node_modules"
# Refresh the anonymous dependency volume from the rebuilt image, so new lockfile
# versions take effect without installing packages on the host or resetting data.
docker compose --project-directory "$PROJECT_ROOT/Web_Application" up -d --build --force-recreate --renew-anon-volumes --wait --wait-timeout 120

echo
echo "The project is ready!"
echo "Website: http://localhost:3000"
echo "  Click Register to create an account, then Log in with it."
echo "  Accounts are saved in PostgreSQL; the sample events come from the Python API."
echo "Stack diagnostic: http://localhost:3000/api/health/database"
echo "  This goes through Vite and Python and checks PostgreSQL with SELECT 1."
echo "  Right-click the address to open it, or copy and paste it into your browser."
echo "Python API docs: http://localhost:8080/docs"
echo "  Try the health endpoint at http://localhost:8080/api/health"
echo "  The original status page is at http://localhost:8080/"
echo "  Auth endpoints: /api/auth/register, /login, /me, /logout. Events: /api/events"
echo "User database: localhost:5432 (PostgreSQL, not a webpage)"
echo "  It stores registered accounts and login sessions, plus two sample users without passwords."
echo "  Open its SQL terminal from the code folder with:"
echo "  docker compose --project-directory User_Database exec database psql -U movie_admin -d movie_users"
echo "  Then type: SELECT * FROM users;  Type \\q to leave."
echo
echo "You can close this terminal; Docker keeps the project running."
echo "Save frontend files to update the browser automatically."
echo "Python .py and .json changes reload the API; refresh the page or request to see its new response."
echo "After dependency or Docker/environment configuration changes, rerun ./start_project.sh."
echo "Database SQL changes still need an explicit migration."
echo "When removing the local setup: ./stop_project.sh"
echo "Stopping deletes the containers and ALL local database users and changes."

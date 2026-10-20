#!/usr/bin/env bash
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

# If a build or startup fails, keep Docker's error visible and explain cleanup.
trap 'echo "Startup did not finish. Read the error above. Run bash stop_project.sh to clean up, then try again."' ERR

echo "Starting the project. The first run downloads images and may take a few minutes."
echo "You do not need to install npm packages yourself."

# Each folder keeps its own Compose setup. --wait waits for healthy services.
# --build rebuilds our app images; --force-recreate replaces old containers.
echo "[1/3] Starting PostgreSQL and creating sample users if the database is empty..."
docker compose --project-directory "$PROJECT_ROOT/User_Database" up -d --build --force-recreate --wait --wait-timeout 120

echo "[2/3] Building and starting the AI backend..."
docker compose --project-directory "$PROJECT_ROOT/AI_Movie_Chatbot" up -d --build --force-recreate --wait --wait-timeout 120

echo "[3/3] Installing React dependencies inside Docker and starting the website..."
docker compose --project-directory "$PROJECT_ROOT/Web_Application" up -d --build --force-recreate --wait --wait-timeout 120

echo
echo "The project is ready!"
echo "Website: http://localhost:3000"
echo "  This is the React movie chat demo. Replies are still sample data."
echo "  Right-click the address to open it, or copy and paste it into your browser."
echo "AI backend: http://localhost:8080"
echo "  Open this in your browser to see the backend's running-status message."
echo "  The AI recommendation feature is not implemented yet."
echo "User database: localhost:5432 (PostgreSQL, not a webpage)"
echo "  It stores two sample users. The apps are not connected to it yet."
echo "  Open its SQL terminal from the repository folder with:"
echo "  docker compose --project-directory User_Database exec database psql -U movie_admin -d movie_users"
echo "  Then type: SELECT * FROM users;  Type \\q to leave."
echo
echo "You can close this terminal; Docker keeps the project running."
echo "After editing app code, run this start command again to rebuild it."
echo "When finished: bash stop_project.sh"
echo "Stopping deletes the containers and ALL local database users and changes."

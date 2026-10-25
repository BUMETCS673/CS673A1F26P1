#!/usr/bin/env bash
# Remove this project's containers, networks, volumes, and locally built images.
# Source files and shared downloaded images (such as PostgreSQL) are kept.
set -u

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is missing. Install and start Docker Desktop first."
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose is missing. Install or update Docker Desktop."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Cannot connect to Docker. Start Docker Desktop and try again."
  exit 1
fi

echo "Removing the project. ALL local database users and changes will be deleted."
echo "Your source code will be kept. The next start creates the sample database again."

# Try every folder even if one cleanup fails, including after a partial startup.
# --volumes deletes database data; --rmi local removes our built app images.
# Never use a global Docker prune: other projects must be left alone.
cleanup_failed=0
for folder in Web_Application AI_Movie_Chatbot User_Database; do
  echo "Removing $folder containers and local data..."
  if ! docker compose --project-directory "$PROJECT_ROOT/$folder" down --volumes --rmi local --remove-orphans; then
    cleanup_failed=1
  fi
done

if [ "$cleanup_failed" -ne 0 ]; then
  echo "Some cleanup failed. Read the errors above and run bash stop_project.sh again."
  exit 1
fi

echo "Project removed. The local database data has been deleted."
echo "To create and start it again: bash start_project.sh"

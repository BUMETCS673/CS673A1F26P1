# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: frontend dev image
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: ran start_project.sh in WSL + Docker, checked localhost:3000, :8080/docs and /api/health/database

# Node includes npm. Teammates do not need either installed on their computer.
FROM node:22-alpine

WORKDIR /app

# Install the exact versions saved in package-lock.json.
# Docker can reuse this step when only our source code changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY index.html ./
COPY vite.config.js ./
COPY src/ ./src/

# This is a local development server, not a production deployment.
EXPOSE 5173
# Listen inside the container so Docker can forward the port to our computer.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]

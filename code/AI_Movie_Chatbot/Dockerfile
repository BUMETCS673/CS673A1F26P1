# AI-USAGE SUMMARY
# Authors: Yuchen Xu (original), Daniel Winnie
# Tools: Yuchen Xu: not yet reported by the author - author to confirm in the AIUsageLog; Daniel's edits: OpenAI Codex (CLI agent), prompted by Daniel Winnie
# Overall AI Contribution: to be confirmed; Daniel's edits ~90%
# AI-Assisted Areas: API image build
# Human Contributions: Yuchen Xu: original Docker setup; Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: ran start_project.sh in WSL + Docker, checked localhost:3000, :8080/docs and /api/health/database

FROM python:3.12-slim

WORKDIR /app

# Cache dependencies separately from application source changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

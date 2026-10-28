# AI-USAGE SUMMARY
# Authors: Daniel Winnie (route), Yung Cheng Chiu (sample data, FV-116)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: GET /api/events route, cached loading, date/time ordering
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep; Yung Cheng Chiu: the six sample events in data/sample_events.json
# Notes/Verification: tests/test_events.py; curl and Swagger /docs

"""FV-116: serve the six fictional Boston sample events from Python."""

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.routes.filter_demo import DemoEvent

router = APIRouter(tags=["events"])

SAMPLE_EVENTS_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_events.json"


def start_time(event: dict) -> datetime:
    """Parse the sample's date and 12-hour Boston time, e.g. 2026-11-01 6:00 PM."""
    return datetime.strptime(f"{event['date']} {event['time']}", "%Y-%m-%d %I:%M %p")


@lru_cache(maxsize=1)
def load_sample_events() -> tuple[dict, ...]:
    """Read the bundled sample file once, soonest event first.

    Sorting here means the order no longer depends on how the file is written.
    """
    with SAMPLE_EVENTS_PATH.open(encoding="utf-8") as sample_file:
        return tuple(sorted(json.load(sample_file)["events"], key=start_time))


@router.get("/events", response_model=list[DemoEvent])
def list_events() -> list[dict]:
    """Return the sample events in start-time order; a real source replaces this later."""
    return list(load_sample_events())

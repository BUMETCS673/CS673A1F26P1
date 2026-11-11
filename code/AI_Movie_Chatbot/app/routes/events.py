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

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.routes.filter_demo import DemoEvent

from app.event_catalog import (
    find_event,
    paginate,
    remove_ended,
    sort_by_start,
)


router = APIRouter(tags=["events"])

class CatalogEvent(BaseModel):
    """Event returned by the event catalog API."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=100)
    title: str = Field(max_length=300)
    category: str = Field(max_length=50)
    start: str
    end: str
    location: str | None = Field(default=None, max_length=300)
    description: str = Field(max_length=2000)


class EventPage(BaseModel):
    """One page of events returned by the catalog API."""

    events: list[CatalogEvent]
    next_offset: int | None

SAMPLE_EVENTS_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_events.json"


@lru_cache(maxsize=1)
def load_sample_events() -> tuple[dict, ...]:
    """Load fictional Boston events from the sample JSON file."""
    with SAMPLE_EVENTS_PATH.open(encoding="utf-8") as sample_file:
        return tuple(json.load(sample_file)["events"])

@router.get("/events", response_model=EventPage)
def list_events(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Return upcoming events in chronological, paginated order."""

    now = datetime.now().astimezone()

    events = list(load_sample_events())
    upcoming = remove_ended(events, now)
    sorted_events = sort_by_start(upcoming)

    return paginate(sorted_events, limit=limit, offset=offset)

@router.get("/events/{event_id}", response_model=CatalogEvent)
def get_event(event_id: str):
    """Return one event by ID."""

    events = list(load_sample_events())
    event = find_event(events, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return event

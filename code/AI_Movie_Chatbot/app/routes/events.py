# AI-USAGE SUMMARY
# Authors: Daniel Winnie (original route), Yung Cheng Chiu (sample data FV-116, catalog helpers FV-122/123), Jibek Kelgenbaeva (paginated list and details routes, FV-122/123)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie (original route, merge fixes); Jibek Kelgenbaeva's tools: to be confirmed by the author
# Overall AI Contribution: ~90% (Daniel's parts); Jibek's part to be confirmed by the author
# AI-Assisted Areas: GET /api/events and GET /api/events/{event_id}; injectable clock for tests
# Human Contributions: Jibek Kelgenbaeva: paginated catalog and details API; Yung Cheng Chiu: sample events and catalog helpers; Daniel Winnie: original route, merge review fixes
# Notes/Verification: tests/test_events.py (fixed reference time, fixture catalog)

"""FV-122/FV-123: upcoming fictional Boston events, one page at a time, plus details."""

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.event_catalog import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    find_event,
    paginate,
    remove_ended,
    sort_by_start,
)

router = APIRouter(tags=["events"])

BOSTON = ZoneInfo("America/New_York")
SAMPLE_EVENTS_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_events.json"


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


def current_time() -> datetime:
    """The moment used to hide ended events. Tests replace this with a fixed time."""
    return datetime.now(BOSTON)


@lru_cache(maxsize=1)
def load_sample_events() -> tuple[dict, ...]:
    """Load the fictional Boston demo events once."""
    with SAMPLE_EVENTS_PATH.open(encoding="utf-8") as sample_file:
        return tuple(json.load(sample_file)["events"])


@router.get("/events", response_model=EventPage)
def list_events(
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """Return upcoming events in start-time order, one page at a time."""
    upcoming = remove_ended(list(load_sample_events()), current_time())
    return paginate(sort_by_start(upcoming), limit=limit, offset=offset)


@router.get("/events/{event_id}", response_model=CatalogEvent)
def get_event(event_id: str) -> dict:
    """Return one event by its stable ID (also used by chat cards and plans)."""
    event = find_event(list(load_sample_events()), event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

"""FV-116: serve the six fictional Boston sample events from Python."""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.routes.filter_demo import DemoEvent

router = APIRouter(tags=["events"])

SAMPLE_EVENTS_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_events.json"


@lru_cache(maxsize=1)
def load_sample_events() -> tuple[dict, ...]:
    """Read the bundled sample file once; it is fictional showcase data."""
    with SAMPLE_EVENTS_PATH.open(encoding="utf-8") as sample_file:
        return tuple(json.load(sample_file)["events"])


@router.get("/events", response_model=list[DemoEvent])
def list_events() -> list[dict]:
    """Return the sample events; a real event source replaces this later."""
    return list(load_sample_events())

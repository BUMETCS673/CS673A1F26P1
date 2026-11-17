# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: GET/PUT/DELETE /api/plans for the signed-in user (FV-95)
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_plans.py (fixture catalog, fixed reference time); tests/live_plans.py

"""FV-95: save events to My Plans, list them, and remove them.

Only event IDs are stored. Listing looks each one up in the current catalog, so
plans always show current details; an event removed from the catalog is counted in
`unavailable_count` instead of being shown.
"""

from datetime import datetime
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import BaseModel

from app import plans
from app.database import DatabaseConfigurationError
from app.event_catalog import find_event, remove_ended, sort_by_start
from app.routes import events as events_route
from app.routes.auth import require_user
from app.routes.events import CatalogEvent

router = APIRouter(tags=["plans"])

CurrentUser = Annotated[dict, Depends(require_user)]
# Catalog IDs are at most 100 characters (see CatalogEvent).
EventId = Annotated[str, Path(min_length=1, max_length=100)]


class Plan(BaseModel):
    """One saved event. `ended` is true once the event's end time has passed."""

    event: CatalogEvent
    saved_at: datetime
    ended: bool


class PlanList(BaseModel):
    """Saved events in start-time order, plus how many are no longer in the catalog."""

    plans: list[Plan]
    unavailable_count: int


def plans_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="My Plans is unavailable right now. Please try again.")


@router.get("/plans", response_model=PlanList)
def list_plans(user: CurrentUser) -> dict:
    """The signed-in user's saved events, ended ones included (the view shows them as Past)."""
    try:
        rows = plans.list_saved(user["id"])
    except (psycopg.Error, DatabaseConfigurationError):
        raise plans_unavailable() from None
    catalog = list(events_route.load_sample_events())
    upcoming_ids = {event["id"] for event in remove_ended(catalog, events_route.current_time())}
    saved_at = {row["event_id"]: row["saved_at"] for row in rows}
    found = [event for event_id in saved_at if (event := find_event(catalog, event_id))]
    return {
        "plans": [
            {"event": event, "saved_at": saved_at[event["id"]], "ended": event["id"] not in upcoming_ids}
            for event in sort_by_start(found)
        ],
        "unavailable_count": len(saved_at) - len(found),
    }


@router.put("/plans/{event_id}", status_code=204, response_class=Response)
def save_plan(event_id: EventId, user: CurrentUser) -> None:
    """Save an upcoming event. Saving it again has the same effect (no duplicate)."""
    catalog = list(events_route.load_sample_events())
    event = find_event(catalog, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if not remove_ended([event], events_route.current_time()):
        raise HTTPException(status_code=409, detail="This event has already ended.")
    try:
        plans.save(user["id"], event_id)
    except (psycopg.Error, DatabaseConfigurationError):
        raise plans_unavailable() from None


@router.delete("/plans/{event_id}", status_code=204, response_class=Response)
def remove_plan(event_id: EventId, user: CurrentUser) -> None:
    """Remove an event from the signed-in user's plans. Works for ended or removed
    events too, and removing something that isn't saved is not an error."""
    try:
        plans.remove(user["id"], event_id)
    except (psycopg.Error, DatabaseConfigurationError):
        raise plans_unavailable() from None

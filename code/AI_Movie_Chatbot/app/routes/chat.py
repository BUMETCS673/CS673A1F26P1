# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: POST /api/chat connecting the FV-124 parser and the FV-122/123 catalog (FV-125); saved chat history (FV-121)
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_chat.py, tests/test_chat_history.py (fixture catalog, fixed reference time); tests/live_chat_history.py

"""FV-125: answer a chat request with matching events from the catalog.
FV-121: save each exchange for the signed-in user and restore it after sign-in."""

from datetime import datetime
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from app import chat, chat_history
from app.database import DatabaseConfigurationError
from app.event_catalog import find_event, remove_ended
from app.routes import events as events_route
from app.routes.auth import require_user
from app.routes.events import CatalogEvent

router = APIRouter(tags=["chat"])

CurrentUser = Annotated[dict, Depends(require_user)]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(strict=True, min_length=1, max_length=1000)


class Interpretation(BaseModel):
    """What the parser understood (the FV-124 fields)."""

    category: str | None
    date: str | None
    time: str | None
    time_operator: str | None
    location: str | None
    location_operator: str | None
    timezone: str | None
    needs_clarification: bool


class ChatReply(BaseModel):
    interpretation: Interpretation
    events: list[CatalogEvent]


class HistoryEntry(ChatReply):
    """One saved exchange. `events` holds only events that are still upcoming, with
    current catalog details; `unavailable_count` counts the ones that ended or were
    removed since."""

    id: int
    request_text: str
    created_at: datetime
    unavailable_count: int


class ChatHistory(BaseModel):
    messages: list[HistoryEntry]


def history_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Chat history is unavailable right now, so this message was not saved. Please try again.",
    )


@router.post("/chat", response_model=ChatReply)
def send_chat(request: ChatRequest, user: CurrentUser) -> dict:
    """Parse the request and return up to 10 upcoming events that match all of it.

    Without a category in the request, the user's preferred categories come first.

    `needs_clarification: true` with no events means the request was not understood;
    an understood request with no events means nothing matches. The exchange is saved
    to the user's history first; if saving fails, the reply is not shown (503).
    """
    now = events_route.current_time()
    # Preferences come from the database on every request, so a Profile change applies at once.
    reply = chat.answer(request.message, list(events_route.load_sample_events()), now,
                        user.get("activity_preferences"))
    try:
        chat_history.save_exchange(
            user["id"], request.message, reply["interpretation"],
            [event["id"] for event in reply["events"]],
        )
    except (psycopg.Error, DatabaseConfigurationError):
        raise history_unavailable() from None
    return reply


@router.get("/chat/history", response_model=ChatHistory)
def get_history(user: CurrentUser) -> dict:
    """The signed-in user's last 50 exchanges, oldest first, with cards rebuilt
    from the current catalog."""
    try:
        rows = chat_history.list_recent(user["id"])
    except (psycopg.Error, DatabaseConfigurationError):
        raise HTTPException(status_code=503, detail="Chat history is unavailable right now.") from None
    upcoming = remove_ended(list(events_route.load_sample_events()), events_route.current_time())
    messages = []
    for row in rows:
        event_ids = row["reply"].get("event_ids", [])
        events = [event for event_id in event_ids if (event := find_event(upcoming, event_id))]
        messages.append({
            "id": row["id"],
            "request_text": row["request_text"],
            "created_at": row["created_at"],
            "interpretation": row["reply"]["interpretation"],
            "events": events,
            "unavailable_count": len(event_ids) - len(events),
        })
    return {"messages": messages}


@router.delete("/chat/history", status_code=204, response_class=Response)
def clear_history(user: CurrentUser) -> None:
    """Delete the signed-in user's chat history (and only theirs)."""
    try:
        chat_history.clear(user["id"])
    except (psycopg.Error, DatabaseConfigurationError):
        raise HTTPException(status_code=503, detail="Chat history could not be cleared. Please try again.") from None

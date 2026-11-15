# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: POST /api/chat connecting the FV-124 parser and the FV-122/123 catalog (FV-125)
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_chat.py (fixture catalog, fixed reference time, login required)

"""FV-125: answer a chat request with matching events from the catalog."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app import chat
from app.routes import events as events_route
from app.routes.events import CatalogEvent

router = APIRouter(tags=["chat"])


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


@router.post("/chat", response_model=ChatReply)
def send_chat(request: ChatRequest) -> dict:
    """Parse the request and return up to 10 upcoming events that match all of it.

    `needs_clarification: true` with no events means the request was not understood;
    an understood request with no events means nothing matches.
    """
    now = events_route.current_time()
    return chat.answer(request.message, list(events_route.load_sample_events()), now)

"""Independent HTTP demo for FV-117; no request-parser dependency."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.event_filters import filter_events

router = APIRouter(tags=["filter demo"])


class DemoEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=100)
    title: str = Field(max_length=300)
    category: str = Field(max_length=50)
    date: str = Field(max_length=10)
    time: str = Field(max_length=50)
    location: str = Field(max_length=300)
    description: str = Field(max_length=2000)


class FilterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str | None = Field(default=None, max_length=50)
    date: str | None = Field(default=None, max_length=10)
    events: list[DemoEvent] = Field(max_length=100)


class FilterResponse(BaseModel):
    message: str
    category: str | None
    date: str | None
    events: list[DemoEvent]


@router.post("/demo/filter-events", response_model=FilterResponse)
def filter_demo(request: FilterRequest) -> FilterResponse:
    """Filter client-supplied fictional samples using explicit category/date.

    This demo is unauthenticated and does not provide an authoritative catalog.
    """
    matches = filter_events(
        [event.model_dump() for event in request.events],
        category=request.category,
        date=request.date,
    )
    return FilterResponse(
        message=(f"Found {len(matches)} matching sample event(s)." if matches
                 else "No sample events match these criteria."),
        category=request.category,
        date=request.date,
        events=matches,
    )

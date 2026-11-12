# AI-USAGE SUMMARY
# Authors: Yung Cheng Chiu
# Tools: to be confirmed by the author (commit tagged [AI])
# Overall AI Contribution: to be confirmed by Yung Cheng Chiu
# AI-Assisted Areas: FV-122/FV-123 catalog helpers (hide ended, sort, find, paginate)
# Human Contributions: Yung Cheng Chiu: catalog rules, fixtures, and review of results
# Notes/Verification: tests/test_event_catalog.py with a fixed reference time

"""Pure catalog helpers: hide ended events, sort by start, find by ID, and paginate."""
from datetime import datetime
from typing import Any

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def _parse_moment(value: str) -> datetime:
    """Parse an ISO 8601 time that includes a UTC offset."""
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"Unreadable event time: {value!r}") from None
    if moment.tzinfo is None:
        raise ValueError(f"Event time needs a UTC offset: {value!r}")
    return moment


def remove_ended(events: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    """Return events whose end is after `now`, in their existing order."""
    if now.tzinfo is None:
        raise ValueError("now must include a time zone")
    return [event for event in events if _parse_moment(event["end"]) > now]


def sort_by_start(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a new list ordered by start moment, then by id for ties."""
    return sorted(events, key=lambda event: (_parse_moment(event["start"]), event["id"]))


def find_event(events: list[dict[str, Any]], event_id: str) -> dict[str, Any] | None:
    """Return the event with exactly this id, or None if there is none."""
    return next((event for event in events if event["id"] == event_id), None)


def paginate(
    events: list[dict[str, Any]],
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict[str, Any]:
    """Return one page of an already sorted list and the offset of the next page."""
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
    if offset < 0:
        raise ValueError("offset must not be negative")
    page = events[offset:offset + limit]
    next_offset = offset + limit
    return {
        "events": page,
        "next_offset": next_offset if next_offset < len(events) else None,
    }
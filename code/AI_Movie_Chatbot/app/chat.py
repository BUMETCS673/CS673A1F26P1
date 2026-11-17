# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: matching parsed chat constraints (FV-124) against the event catalog (FV-122/123) for FV-125; shared place matching and preference order (FV-127) wired in
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_chat.py with a fixed Boston reference time and the fixture catalog

"""Turn a chat message into matching catalog events. Pure functions, no HTTP or SQL.

The FV-124 parser returns constraints (category, date, time, location); this module
keeps the upcoming catalog events that satisfy all of them, in start-time order.
"""

from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.event_catalog import remove_ended, sort_by_start
from app.place_matching import location_matches
from app.preference_order import order_by_preferences
from app.request_parser import parse_event_request

BOSTON = ZoneInfo("America/New_York")
MAX_RESULTS = 10


def _boston(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(BOSTON)


def _on_date(event: dict[str, Any], day: str) -> bool:
    """True if the event is happening at any point on this Boston calendar day."""
    start = _boston(event["start"])
    # An event ending exactly at midnight does not belong to the next day.
    last_day = (_boston(event["end"]) - timedelta(microseconds=1)).date()
    return start.date() <= date.fromisoformat(day) <= max(start.date(), last_day)


def _matches_time(event: dict[str, Any], clock: str, operator: str | None) -> bool:
    """Compare the event's Boston start time with "after/before/at HH:MM"."""
    start = _boston(event["start"]).time().replace(second=0, microsecond=0)
    wanted = time.fromisoformat(clock)
    if operator == "after":
        return start >= wanted
    if operator == "before":
        return start < wanted
    return start == wanted


def find_matches(
    interpretation: dict[str, Any], events: list[dict[str, Any]], now: datetime,
    preferences: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Up to MAX_RESULTS upcoming events that satisfy every parsed constraint.

    Soonest first. When the request names no category, events in the user's
    preferred categories come first (FV-127); that ordering happens before the
    cut to MAX_RESULTS, so a preferred event later in the month is not dropped.
    """
    if interpretation.get("needs_clarification"):
        return []
    category = (interpretation.get("category") or "").casefold()
    matches = []
    for event in sort_by_start(remove_ended(events, now)):
        if category and event["category"].casefold() != category:
            continue
        if interpretation.get("date") and not _on_date(event, interpretation["date"]):
            continue
        if interpretation.get("time") and not _matches_time(
            event, interpretation["time"], interpretation.get("time_operator"),
        ):
            continue
        if interpretation.get("location") and not location_matches(
            event.get("location"), interpretation["location"],
        ):
            continue
        matches.append(event)
    return order_by_preferences(matches, preferences, interpretation.get("category"))[:MAX_RESULTS]


def answer(
    message: str, events: list[dict[str, Any]], now: datetime, preferences: list[str] | None = None,
) -> dict[str, Any]:
    """The chat reply: what the parser understood plus the matching events."""
    interpretation = parse_event_request(message, now=now)
    return {
        "interpretation": interpretation,
        "events": find_matches(interpretation, events, now, preferences),
    }

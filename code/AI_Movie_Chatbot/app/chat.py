# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: matching parsed chat constraints (FV-124) against the event catalog (FV-122/123) for FV-125
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


def _normalize_place(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def matches_place(event: dict[str, Any], place: str) -> bool:
    """"near Fenway" matches a location containing "Fenway", ignoring case and spaces.

    Interim rule from the team's proposed defaults. Ji's place-matching ticket will
    replace this with the shared helper; events without a location never match.
    """
    wanted = _normalize_place(place)
    return bool(wanted) and wanted in _normalize_place(event.get("location"))


def find_matches(
    interpretation: dict[str, Any], events: list[dict[str, Any]], now: datetime,
) -> list[dict[str, Any]]:
    """Upcoming events that satisfy every parsed constraint, soonest first."""
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
        if interpretation.get("location") and not matches_place(event, interpretation["location"]):
            continue
        matches.append(event)
    return matches[:MAX_RESULTS]


def answer(message: str, events: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    """The chat reply: what the parser understood plus the matching events."""
    interpretation = parse_event_request(message, now=now)
    return {
        "interpretation": interpretation,
        "events": find_matches(interpretation, events, now),
    }

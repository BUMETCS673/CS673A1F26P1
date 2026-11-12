# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: OpenAI Codex, prompted by Ji Wu
# Overall AI Contribution: 80%
# AI-Assisted Areas: request grammar (FV-118); Codex implementation and tests for FV-124
# Human Contributions: Ji Wu: requirements, prompts, scope decisions, and review of results
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""Parse Boston event requests without a model or catalog lookup."""

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


BOSTON_TIMEZONE = "America/New_York"
BOSTON = ZoneInfo(BOSTON_TIMEZONE)
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

_DAY = "|".join((*WEEKDAYS, "today", "tomorrow"))
_FLAGS = re.IGNORECASE | re.ASCII
_CATEGORY = re.compile(r"(music|arts|food|outdoors|social)(?= |$)", _FLAGS)
_GENERIC = re.compile(r"(?:something fun|events)(?= |$)", _FLAGS)
_DATE = re.compile(
    rf"(?:on )?(?:(?P<iso>[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})|"
    rf"(?:(?P<week>this|next) )?(?P<day>{_DAY}))(?= |$)",
    _FLAGS,
)
_TIME = re.compile(
    r"(after|before|at) ([0-9]{1,2})(?::([0-9]{2}))?(?: ?(am|pm))?(?= |$)",
    _FLAGS,
)
_LOCATION = re.compile(r"(in|near) ", _FLAGS)
_CLAUSE_START = re.compile(
    rf" (?:on|this|next|{_DAY}|after|before|at|in|near|[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})\b",
    _FLAGS,
)
_PLACE_WORD = r"[^\W\d_]+(?:[-'’][^\W\d_]+)*"
_PLACE_NAME = re.compile(rf"{_PLACE_WORD}(?:(?:, ?| ){_PLACE_WORD})*")
_AMBIGUOUS_PLACE = re.compile(r"\b(?:and|or|not|except)\b", _FLAGS)


def _resolve_date(match: re.Match[str], now: datetime | None) -> str:
    if match["iso"]:
        return date.fromisoformat(match["iso"]).isoformat()

    today = (datetime.now(BOSTON) if now is None else now.astimezone(BOSTON)).date()
    day = match["day"].lower()
    week = match["week"].lower() if match["week"] else None
    if day in ("today", "tomorrow"):
        if week:
            raise ValueError("Unexpected week qualifier")
        offset = int(day == "tomorrow")
    elif week == "next":
        # "Next Friday" is Friday of the next Monday-Sunday calendar week.
        offset = 7 - today.weekday() + WEEKDAYS.index(day)
    else:
        # A bare weekday or "this Friday" means the next occurrence, including today.
        offset = (WEEKDAYS.index(day) - today.weekday()) % 7
    return (today + timedelta(days=offset)).isoformat()


def _resolve_time(match: re.Match[str]) -> str:
    hour = int(match[2])
    minute = int(match[3] or 0)
    if match[4]:
        if not 1 <= hour <= 12:
            raise ValueError("Hour outside the 12-hour clock")
        hour = hour % 12 + (12 if match[4].lower() == "pm" else 0)
    elif match[3] is None:
        raise ValueError("Specify AM/PM or use HH:MM")
    return time(hour, minute).isoformat(timespec="minutes")


def parse_event_request(
    message: str, *, now: datetime | None = None,
) -> dict[str, str | bool | None]:
    """Return normalized constraints, or request clarification for unsupported text.

    An optional category can be followed by date, time, and location clauses in
    any order. For tests, supply a timezone-aware reference instant as `now`.
    """
    if now is not None and now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    clarification: dict[str, str | bool | None] = dict.fromkeys(
        ("category", "date", "time", "time_operator", "location", "location_operator", "timezone"),
    )
    clarification["needs_clarification"] = True
    result = {**clarification, "timezone": BOSTON_TIMEZONE, "needs_clarification": False}
    remaining = " ".join(message.split())

    if category := _CATEGORY.match(remaining):
        result["category"] = category[1].capitalize()
        remaining = remaining[category.end():].lstrip()
    elif generic := _GENERIC.match(remaining):
        remaining = remaining[generic.end():].lstrip()

    try:
        while remaining:
            if (matched := _DATE.match(remaining)) and result["date"] is None:
                result["date"] = _resolve_date(matched, now)
            elif (matched := _TIME.match(remaining)) and result["time"] is None:
                result["time"] = _resolve_time(matched)
                result["time_operator"] = matched[1].lower()
            elif (matched := _LOCATION.match(remaining)) and result["location"] is None:
                tail = remaining[matched.end():]
                next_clause = _CLAUSE_START.search(tail)
                end = next_clause.start() if next_clause else len(tail)
                place = tail[:end]
                if not _PLACE_NAME.fullmatch(place) or _AMBIGUOUS_PLACE.search(place):
                    return clarification
                result["location"] = place
                result["location_operator"] = matched[1].lower()
                remaining = tail[end:].lstrip()
                continue
            else:
                return clarification
            remaining = remaining[matched.end():].lstrip()
    except (ValueError, OverflowError):
        return clarification

    if not any(result[key] is not None for key in ("category", "date", "time", "location")):
        return clarification
    return result

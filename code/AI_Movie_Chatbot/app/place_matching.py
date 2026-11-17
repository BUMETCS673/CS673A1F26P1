# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over place matching from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: shared "near X" / "in X" place matching for chat requests
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_place_matching.py (fixture catalog, fixed Boston time); tests/test_chat.py

"""Place matching for chat requests such as "food near the North End".

The team's agreed rule: "near X" matches any event whose location contains X,
ignoring case. This helper applies it on whole words after tidying both sides, so
everyday wording works too:

- case, extra spaces, hyphens, and punctuation are ignored ("north-end" = "North End");
- a leading "the" is ignored ("the North End");
- a landmark inside a neighborhood matches it ("Fenway Park" -> "Fenway, Boston"),
  because the event's neighborhood (the part before the first comma) appears in the
  request as whole words.

Matching is on whole words, so "ston" does not match "Boston". Events without a
location never match, and an unknown place matches nothing (an honest "no matches").
"""

import re
from typing import Any

_NOT_WORD = re.compile(r"[^\w]+")


def normalize_place(value: str | None) -> str:
    """Lowercase words separated by single spaces, without a leading "the"."""
    words = _NOT_WORD.sub(" ", (value or "").casefold()).split()
    if words[:1] == ["the"]:
        words = words[1:]
    return " ".join(words)


def _contains_words(text: str, words: str) -> bool:
    return bool(words) and f" {words} " in f" {text} "


def location_matches(location: str | None, place: str | None) -> bool:
    """True if an event at `location` matches a request for `place`."""
    wanted = normalize_place(place)
    where = normalize_place(location)
    if not wanted or not where:
        return False
    neighborhood = normalize_place((location or "").split(",")[0])
    return _contains_words(where, wanted) or _contains_words(wanted, neighborhood)


def filter_by_place(events: list[dict[str, Any]], place: str | None) -> list[dict[str, Any]]:
    """The events (in their existing order) whose location matches `place`."""
    return [event for event in events if location_matches(event.get("location"), place)]

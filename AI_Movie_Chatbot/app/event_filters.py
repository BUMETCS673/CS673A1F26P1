# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: not yet reported by the author - author to confirm in the AIUsageLog
# Overall AI Contribution: to be confirmed by Ji Wu
# AI-Assisted Areas: category/date filter (FV-117)
# Human Contributions: Ji Wu: implementation and tests (FV-117 / FV-118)
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""Filter caller-supplied events without changing the catalog or its order."""

from typing import Any


def filter_events(
    events: list[dict[str, Any]],
    category: str | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    """Return events matching every supplied filter; dates match exactly.

    Categories are case-insensitive. The result is a new list containing the
    original event dictionaries, which this helper only reads.
    """
    category_key = category.casefold() if category is not None else None
    return [
        event
        for event in events
        if (category_key is None or event["category"].casefold() == category_key)
        and (date is None or event["date"] == date)
    ]

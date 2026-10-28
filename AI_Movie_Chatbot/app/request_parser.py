# AI-USAGE SUMMARY
# Authors: Ji Wu
# Tools: not yet reported by the author - author to confirm in the AIUsageLog
# Overall AI Contribution: to be confirmed by Ji Wu
# AI-Assisted Areas: category / 'on YYYY-MM-DD' request grammar (FV-118)
# Human Contributions: Ji Wu: implementation and tests (FV-117 / FV-118)
# Notes/Verification: behaviour covered by the unit tests in AI_Movie_Chatbot/tests; merged via PRs #11/#12

"""Recognize the starter request grammar without models or catalog access."""

import re
from datetime import date


def parse_event_request(message: str) -> dict[str, str | bool | None]:
    """Accept a category, optionally followed by 'on YYYY-MM-DD'.

    Anything outside that complete grammar requests clarification instead of
    silently discarding a user's additional constraints.
    """
    clarification = {"category": None, "date": None, "needs_clarification": True}
    match = re.fullmatch(
        r"(music|arts|food|outdoors|social)(?: on ([0-9]{4}-[0-9]{2}-[0-9]{2}))?",
        message.strip(),
        flags=re.IGNORECASE | re.ASCII,
    )
    if match is None:
        return clarification

    category, requested_date = match.groups()
    if requested_date is not None:
        try:
            date.fromisoformat(requested_date)
        except ValueError:
            return clarification

    return {
        "category": category.capitalize(),
        "date": requested_date,
        "needs_clarification": False,
    }

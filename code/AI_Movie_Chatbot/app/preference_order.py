# AI-USAGE SUMMARY
# Authors: Yung Cheng Chiu
# Tools: Claude (Anthropic), prompted by Yung Cheng Chiu
# Overall AI Contribution: ~90%
# AI-Assisted Areas: FV-127 preference-order helper
# Human Contributions: Yung Cheng Chiu: requirements from Jira FV-127, rule decision (preferred categories first, nothing removed), prompts, running the tests, review of results
# Notes/Verification: tests/test_preference_order.py with the catalog fixtures and a fixed reference time

"""FV-127: put a user's preferred categories first when a chat request names none.

Like event_catalog.py, this is a pure helper: it only reads the list it is given
and returns a new one. The chat route will call it after remove_ended() and
sort_by_start(), passing the parsed request's category (None when the user said
something generic such as "something fun this weekend") and the signed-in user's
activity_preferences.
"""

from typing import Any, Iterable


def order_by_preferences(
    events: list[dict[str, Any]],
    preferred_categories: Iterable[str] | None,
    requested_category: str | None = None,
) -> list[dict[str, Any]]:
    """Return a new list with preferred-category events first; nothing is removed.

    - If the request already names a category, the list is returned unchanged
      (as a copy): the user asked for that category, so preferences do not apply.
    - Otherwise events whose category is in the preferences come first, then all
      other events. Each group keeps the order it had in the input, so a list
      that was sorted by start time stays sorted within each group.
    - Category matching ignores case. An empty or missing preference list, or
      preferences that match no event, leave the order as it was.
    """
    if requested_category is not None or not preferred_categories:
        return list(events)

    preferred = {category.casefold() for category in preferred_categories}
    is_preferred = [event["category"].casefold() in preferred for event in events]
    return (
        [event for event, keep in zip(events, is_preferred) if keep]
        + [event for event, keep in zip(events, is_preferred) if not keep]
    )
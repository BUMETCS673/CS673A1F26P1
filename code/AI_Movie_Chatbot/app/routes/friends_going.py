# AI-USAGE SUMMARY
# Authors: Daniel Winnie (taking over "friends going" from the Iteration 2 plan)
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: friends going on an event and a friend's upcoming plans, mutual follows only
# Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_friends_going.py (fake storage); tests/live_friends_going.py (three accounts, PostgreSQL)

"""Friends going: which friends saved an event, and a friend's upcoming plans.

A friend is a mutual follow: you follow them and they follow you. Anyone else,
including a one-way follower, sees nothing. Both checks run on every request, so
unfollowing removes access immediately.
"""

from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from app import plans
from app.database import DatabaseConfigurationError
from app.event_catalog import find_event, remove_ended, sort_by_start
from app.routes import events as events_route
from app.routes.auth import require_user
from app.routes.events import CatalogEvent
from app.routes.follows import PublicUser

router = APIRouter(tags=["friends going"])

CurrentUser = Annotated[dict, Depends(require_user)]
EventId = Annotated[str, Path(min_length=1, max_length=100)]
UserId = Annotated[int, Path(ge=1, le=2_147_483_647)]


class FriendsGoing(BaseModel):
    friends: list[PublicUser]


class FriendPlan(BaseModel):
    event: CatalogEvent


class FriendPlans(BaseModel):
    friend: PublicUser
    plans: list[FriendPlan]


def unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="Friends' plans are unavailable right now. Please try again.")


@router.get("/events/{event_id}/friends-going", response_model=FriendsGoing)
def friends_going(event_id: EventId, user: CurrentUser) -> dict:
    """Mutual follows who saved this event. An empty list means none."""
    if find_event(list(events_route.load_sample_events()), event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        return {"friends": plans.friends_going(user["id"], event_id)}
    except (psycopg.Error, DatabaseConfigurationError):
        raise unavailable() from None


@router.get("/friends/{user_id}/plans", response_model=FriendPlans)
def friend_plans(user_id: UserId, user: CurrentUser) -> dict:
    """A mutual follow's upcoming saved events in start order.

    404 for anyone who is not a mutual follow (including unknown accounts and
    yourself), so the answer never reveals whether an account exists.
    """
    try:
        friend = None if user_id == user["id"] else plans.mutual_friend(user["id"], user_id)
        if friend is None:
            raise HTTPException(status_code=404, detail="Friend not found")
        rows = plans.list_saved(user_id)
    except (psycopg.Error, DatabaseConfigurationError):
        raise unavailable() from None
    upcoming = remove_ended(list(events_route.load_sample_events()), events_route.current_time())
    found = [event for row in rows if (event := find_event(upcoming, row["event_id"]))]
    return {"friend": friend, "plans": [{"event": event} for event in sort_by_start(found)]}

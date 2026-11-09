# AI-USAGE SUMMARY
# Authors: Yuchen Xu (feature requirements)
# Tools: OpenAI Codex
# Overall AI Contribution: Codex drafted this module.
# AI-Assisted Areas: FastAPI routes, public response model, and session integration.
# Human Contributions: Yuchen Xu confirmed the one-way follow model.
# Notes/Verification: tests/live_follows.py covers the authenticated follow flow.

"""Authenticated search, following, and followers for the signed-in account."""

from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from pydantic import BaseModel

from app import follows
from app.database import DatabaseConfigurationError
from app.routes.auth import require_user

router = APIRouter(tags=["follows"])

CurrentUser = Annotated[dict, Depends(require_user)]
UserId = Annotated[int, Path(ge=1, le=2_147_483_647)]


class PublicUser(BaseModel):
    id: int
    username: str
    display_name: str | None


def database_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="The follow service is unavailable.")


@router.get("/users/search", response_model=list[PublicUser])
def search_users(
    user: CurrentUser, username: Annotated[str, Query(min_length=1, max_length=50)]
) -> list[dict]:
    """Find another account by exact username, ignoring case."""
    try:
        return follows.search_users(username.strip(), user["id"])
    except (psycopg.Error, DatabaseConfigurationError):
        raise database_unavailable() from None


@router.get("/following", response_model=list[PublicUser])
def list_following(user: CurrentUser) -> list[dict]:
    """Return the people the current account follows."""
    try:
        return follows.list_following(user["id"])
    except (psycopg.Error, DatabaseConfigurationError):
        raise database_unavailable() from None


@router.get("/followers", response_model=list[PublicUser])
def list_followers(user: CurrentUser) -> list[dict]:
    """Return the people who follow the current account."""
    try:
        return follows.list_followers(user["id"])
    except (psycopg.Error, DatabaseConfigurationError):
        raise database_unavailable() from None


@router.put("/following/{user_id}", status_code=204, response_class=Response)
def follow(user_id: UserId, user: CurrentUser) -> None:
    """Follow the target account. A repeat request has the same effect."""
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")
    try:
        follows.add_follow(user["id"], user_id)
    except psycopg.errors.ForeignKeyViolation as error:
        if error.diag.constraint_name == "user_follows_followed_id_fkey":
            raise HTTPException(status_code=404, detail="User not found.") from None
        raise database_unavailable() from None
    except (psycopg.Error, DatabaseConfigurationError):
        raise database_unavailable() from None


@router.delete("/following/{user_id}", status_code=204, response_class=Response)
def unfollow(user_id: UserId, user: CurrentUser) -> None:
    """Remove only the current account's follow of the target, if it exists."""
    try:
        follows.remove_follow(user["id"], user_id)
    except (psycopg.Error, DatabaseConfigurationError):
        raise database_unavailable() from None

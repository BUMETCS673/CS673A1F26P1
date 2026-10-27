"""Registration, login, current user, and logout with server-side sessions.

The browser receives an HttpOnly cookie that JavaScript cannot read. The
database stores only a hash of it, and logging out deletes the session.
"""

import os
import re
from typing import Literal

import psycopg
from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app import users
from app.database import DatabaseConfigurationError
from app.passwords import DUMMY_HASH, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE = "session"
ActivityPreference = Literal["Music", "Arts", "Food", "Outdoors", "Social"]
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{3,50}")
# A light shape check; confirming ownership of an address needs email delivery.
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
DATABASE_UNAVAILABLE = "The account service is unavailable. Check that the database is running."


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)
    activity_preferences: list[ActivityPreference] = Field(max_length=5)

    @field_validator("username")
    @classmethod
    def check_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_PATTERN.fullmatch(value):
            raise ValueError("Username must be 3-50 letters, numbers, periods, underscores, or hyphens.")
        return value

    @field_validator("display_name")
    @classmethod
    def check_display_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Display name is required.")
        return value.strip()

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return value

    @field_validator("activity_preferences")
    @classmethod
    def check_preferences(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Choose at least one activity preference.")
        return list(dict.fromkeys(value))


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str | None
    email: str
    activity_preferences: list[str]


def _database_unavailable() -> HTTPException:
    # Driver messages can contain credentials or host details: keep them private.
    return HTTPException(status_code=503, detail=DATABASE_UNAVAILABLE)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE, token,
        max_age=int(users.SESSION_LIFETIME.total_seconds()),
        httponly=True, samesite="lax", path="/api",
        # Local development uses plain HTTP; set SESSION_COOKIE_SECURE=true behind HTTPS.
        secure=os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true",
    )


@router.post("/register", response_model=UserResponse, status_code=201,
             responses={409: {"description": "Username or email already registered"},
                        503: {"description": "Database unavailable"}})
def register(request: RegisterRequest) -> dict:
    """Create an account. The client logs in afterwards with the same credentials."""
    try:
        return users.create_user(request.username, request.email, request.display_name,
                                 hash_password(request.password), request.activity_preferences)
    except users.DuplicateAccountError as error:
        raise HTTPException(status_code=409,
                            detail=f"That {error.field} is already registered.") from None
    except (psycopg.Error, DatabaseConfigurationError):
        raise _database_unavailable() from None


@router.post("/login", response_model=UserResponse,
             responses={401: {"description": "Incorrect username or password"},
                        503: {"description": "Database unavailable"}})
def login(request: LoginRequest, response: Response) -> dict:
    """Check the password and start a session stored in an HttpOnly cookie."""
    try:
        found = users.find_login(request.username.strip())
        user, stored_hash = found if found else (None, DUMMY_HASH)
        # Always hash, so unknown usernames cannot be detected by response time.
        if not verify_password(request.password, stored_hash) or user is None:
            raise HTTPException(status_code=401, detail="Incorrect username or password.")
        _set_session_cookie(response, users.create_session(user["id"]))
    except (psycopg.Error, DatabaseConfigurationError):
        raise _database_unavailable() from None
    return user


@router.get("/me", response_model=UserResponse,
            responses={401: {"description": "Not logged in"},
                       503: {"description": "Database unavailable"}})
def current_user(session: str | None = Cookie(default=None, max_length=200)) -> dict:
    """Return the user for this browser's session, so a reload stays logged in."""
    try:
        user = users.get_session_user(session) if session else None
    except (psycopg.Error, DatabaseConfigurationError):
        raise _database_unavailable() from None
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return user


@router.post("/logout", status_code=204, response_class=Response)
def logout(response: Response, session: str | None = Cookie(default=None, max_length=200)) -> None:
    """End the session. The cookie is cleared even if the database is unreachable."""
    response.delete_cookie(SESSION_COOKIE, path="/api", httponly=True, samesite="lax")
    if session:
        try:
            users.delete_session(session)
        except (psycopg.Error, DatabaseConfigurationError):
            # The browser no longer holds the token; the row expires on its own.
            pass

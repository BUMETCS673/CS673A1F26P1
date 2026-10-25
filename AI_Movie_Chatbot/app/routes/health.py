"""Liveness checks confirm that the API can serve requests."""

from typing import Literal

import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import DatabaseConfigurationError, get_connection

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report API liveness independently of databases and external services."""
    return HealthResponse(status="ok")


class DatabaseHealthResponse(HealthResponse):
    database: Literal["ok"]


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    responses={503: {"description": "Database unavailable or misconfigured"}},
)
def database_health() -> DatabaseHealthResponse:
    """Check a real database round trip without reading any user records."""
    # A regular def runs blocking database I/O in FastAPI's worker thread pool.
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise psycopg.DatabaseError("Unexpected diagnostic result")
    except (psycopg.Error, DatabaseConfigurationError):
        # Driver messages can contain credentials or host details: keep them private.
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check the backend configuration and database service.",
        ) from None
    return DatabaseHealthResponse(status="ok", database="ok")

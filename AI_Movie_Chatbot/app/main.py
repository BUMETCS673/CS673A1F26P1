"""Assemble the API. Importing this module does not start a server."""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.routes import auth, events, filter_demo, health, parser_demo


def create_app() -> FastAPI:
    """Create an independent application for Uvicorn or tests."""
    application = FastAPI(
        title="Event Planning API",
        description="API foundation for the team's event-planning application.",
        version="0.1.0",
    )
    application.include_router(health.router, prefix="/api")
    application.include_router(filter_demo.router, prefix="/api")
    application.include_router(parser_demo.router, prefix="/api")
    application.include_router(events.router, prefix="/api")
    application.include_router(auth.router, prefix="/api")

    @application.get("/", response_class=PlainTextResponse, include_in_schema=False)
    async def status() -> str:
        # Keep the existing startup page useful while features are added.
        return "AI Movie Recommendation Chatbot is running"

    return application


app = create_app()

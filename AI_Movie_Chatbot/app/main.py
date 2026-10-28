# AI-USAGE SUMMARY
# Authors: Daniel Winnie, Ji Wu, Yuchen Xu (original Docker app)
# Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (router registration for events/auth); Ji Wu's demo-router lines: not yet reported by the author - author to confirm in the AIUsageLog
# Overall AI Contribution: ~85% (Daniel's parts)
# AI-Assisted Areas: application factory and router registration
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep; Ji Wu: registered the FV-117/118 demo routers
# Notes/Verification: unit tests in AI_Movie_Chatbot/tests (65 passing), manual checks in Swagger /docs

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
        return "Boston Events Planner API is running"

    return application


app = create_app()

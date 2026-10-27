"""Independent HTTP demo for FV-118; no catalog or filter dependency."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.request_parser import parse_event_request

router = APIRouter(tags=["parser demo"])


class ParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(strict=True, max_length=1000)


class ParseResponse(BaseModel):
    category: str | None
    date: str | None
    needs_clarification: bool


@router.post("/demo/parse-event-request", response_model=ParseResponse)
def parser_demo(request: ParseRequest) -> ParseResponse:
    """Return the starter parser's exact three fields, without searching events.

    This unauthenticated demo has no model, database, or catalog dependency.
    """
    return ParseResponse(**parse_event_request(request.message))

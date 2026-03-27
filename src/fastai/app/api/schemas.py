"""Request and response schemas for HTTP transport layer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Incoming AI query payload."""

    query: str = Field(min_length=1, max_length=10_000)
    debug: bool = False


class Source(BaseModel):
    """Source citation payload."""

    id: str
    text: str
    metadata: dict[str, object] = Field(default_factory=dict)


class DebugPayload(BaseModel):
    """Optional debug output fields for traceability."""

    retrieved_chunks: list[dict[str, object]]
    context: str
    final_prompt: str


class AskResponse(BaseModel):
    """Base response shape for AI query execution."""

    answer: str
    sources: list[Source] = Field(default_factory=list)
    debug: DebugPayload | None = None


class ErrorResponse(BaseModel):
    """Stable error response shape exposed over HTTP."""

    code: str
    message: str
    request_id: str

    model_config = ConfigDict(extra="forbid")

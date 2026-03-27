"""HTTP routers for FastAI API surface."""

from __future__ import annotations

from fastapi import APIRouter

from .schemas import AskRequest, AskResponse

api_router = APIRouter()


@api_router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    """Handle ask requests with a temporary deterministic response."""
    return _run_ask(payload)


def _run_ask(payload: AskRequest) -> AskResponse:
    """Internal ask executor extracted for easy test patching."""
    return AskResponse(answer=f"Query received: {payload.query}", sources=[])

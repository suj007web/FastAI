"""HTTP routers for FastAI API surface."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from .schemas import AskRequest, AskResponse

api_router = APIRouter()
API_KEY_HEADER = "X-API-Key"


@api_router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
) -> AskResponse:
    """Handle ask requests through the runtime orchestration pipeline."""
    _enforce_auth_mode(x_api_key)
    return _run_ask(payload)


def _run_ask(payload: AskRequest) -> AskResponse:
    """Internal ask executor extracted for easy test patching."""
    from ...sdk import FastAI

    sdk = FastAI.from_env()
    return sdk.ask_payload(payload)


def _enforce_auth_mode(provided_api_key: str | None) -> None:
    from ...sdk import FastAI

    auth_config = FastAI.from_env().config.auth
    mode = (auth_config.mode or "disabled").strip().lower()

    if mode == "disabled":
        return

    if mode == "api_key":
        configured_key = (auth_config.api_key or "").strip()
        if not provided_api_key:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthorized", "message": "Missing API key."},
            )
        if not configured_key or provided_api_key != configured_key:
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Invalid API key."},
            )
        return

    raise HTTPException(
        status_code=500,
        detail={"code": "auth_config_error", "message": "Unsupported auth mode."},
    )

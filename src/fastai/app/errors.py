"""Global exception handling for FastAI transport layer."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.schemas import ErrorResponse


def _request_id_from(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) and request_id else "unknown"


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers with stable response envelopes."""

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        _: RequestValidationError,
    ) -> JSONResponse:
        payload = ErrorResponse(
            code="invalid_request",
            message="Invalid request payload",
            request_id=_request_id_from(request),
        )
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _: Exception) -> JSONResponse:
        payload = ErrorResponse(
            code="internal_error",
            message="Internal server error",
            request_id=_request_id_from(request),
        )
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )

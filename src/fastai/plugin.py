"""Router plugin integration entrypoints for host applications."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from .sdk import FastAI


def get_fastai_router(*, sdk: FastAI) -> APIRouter:
    """Return mountable FastAI router for host app plugin integration."""
    return sdk.get_router()


def mount_fastai_router(app: FastAPI, *, sdk: FastAI, path: str = "/ai") -> None:
    """Mount FastAI routes under a configurable namespace path."""
    app.include_router(get_fastai_router(sdk=sdk), prefix=path)

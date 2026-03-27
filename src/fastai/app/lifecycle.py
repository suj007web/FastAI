"""Application lifecycle hooks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set and clear simple runtime lifecycle state."""
    app.state.started = True
    try:
        yield
    finally:
        app.state.started = False

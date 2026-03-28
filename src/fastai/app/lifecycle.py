"""Application lifecycle hooks."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

LOGGER = logging.getLogger("fastai.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set and clear simple runtime lifecycle state."""
    if hasattr(app.state, "settings") and hasattr(app.state.settings, "summary"):
        app.state.config_summary = app.state.settings.summary()
        LOGGER.info("FastAI startup config summary: %s", app.state.config_summary)

    app.state.started = True
    try:
        yield
    finally:
        app.state.started = False

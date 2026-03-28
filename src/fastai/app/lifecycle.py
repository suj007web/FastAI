"""Application lifecycle hooks."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .ingestion_watcher import DocsIngestionWatcher

LOGGER = logging.getLogger("fastai.app")


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _parse_float(value: str | None, *, default: float) -> float:
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    if parsed <= 0:
        return default
    return parsed


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Set and clear simple runtime lifecycle state."""
    if hasattr(app.state, "settings") and hasattr(app.state.settings, "summary"):
        app.state.config_summary = app.state.settings.summary()
        LOGGER.info("FastAI startup config summary: %s", app.state.config_summary)

    watch_docs = _parse_bool(os.getenv("FASTAI_INGESTION_WATCH_DOCS"), default=False)
    docs_path = Path(os.getenv("FASTAI_INGESTION_WATCH_PATH", "docs")).resolve()
    poll_interval_sec = _parse_float(
        os.getenv("FASTAI_INGESTION_WATCH_INTERVAL_SEC"),
        default=2.0,
    )
    debounce_sec = _parse_float(
        os.getenv("FASTAI_INGESTION_WATCH_DEBOUNCE_SEC"),
        default=1.0,
    )

    watcher: DocsIngestionWatcher | None = None
    if watch_docs:
        def _ingest_docs() -> None:
            from fastai.sdk import FastAI

            sdk = FastAI.from_env()
            summary = sdk.add_data(str(docs_path))
            LOGGER.info(
                "Auto-ingestion completed for docs path '%s': %s",
                docs_path,
                summary,
            )

        watcher = DocsIngestionWatcher(
            docs_path=docs_path,
            on_change=_ingest_docs,
            poll_interval_sec=poll_interval_sec,
            debounce_sec=debounce_sec,
        )
        watcher.start()
        app.state.docs_watcher = watcher
        LOGGER.info(
            "Docs watcher enabled for '%s' (poll_interval_sec=%.2f, debounce_sec=%.2f).",
            docs_path,
            poll_interval_sec,
            debounce_sec,
        )

    app.state.started = True
    try:
        yield
    finally:
        if watcher is not None:
            watcher.stop()
        app.state.started = False

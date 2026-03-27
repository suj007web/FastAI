"""Minimal application entrypoint for FastAI."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .api import api_router
from .errors import register_exception_handlers
from .lifecycle import lifespan
from .middleware import register_request_id_middleware
from .settings import AppSettings


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create the FastAPI application with runtime settings and lifecycle hooks."""
    resolved_settings = settings or AppSettings.from_env()
    app = FastAPI(title="FastAI Framework", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved_settings

    register_request_id_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"name": "fastai-framework", "status": "initialized"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": resolved_settings.env}

    return app


def main() -> None:
    """CLI entrypoint used by the package script."""
    settings = AppSettings.from_env()
    uvicorn.run(
        "fastai.app.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()

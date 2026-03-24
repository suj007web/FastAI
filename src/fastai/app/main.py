"""Minimal application entrypoint for FastAI."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create a minimal FastAPI app for bootstrap and Docker runtime checks."""
    app = FastAPI(title="FastAI Framework", version="0.1.0")

    @app.get("/")
    def root() -> dict[str, str]:
        return {"name": "fastai-framework", "status": "initialized"}

    return app


def main() -> None:
    """CLI entrypoint used by the package script."""
    uvicorn.run("fastai.app.main:create_app", factory=True, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

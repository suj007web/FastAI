"""Developer-first FastAI SDK facade."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast

from fastapi import APIRouter, FastAPI

from .ai_app import AIApp, RouteHandler
from .app.api.schemas import AskRequest, AskResponse
from .config import FastAIConfig, resolve_config


class FastAI:
    """Facade that wraps runtime config, AI routes, and host integration hooks."""

    def __init__(
        self,
        *,
        config: FastAIConfig | None = None,
        profile: str | None = None,
        vector_backend: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        provider_credential: str | None = None,
        **overrides: object,
    ) -> None:
        constructor_overrides: dict[str, object] = {
            "profile": profile,
            "vector_backend": vector_backend,
            "model": model,
            "provider": provider,
            "provider_credential": provider_credential,
        }
        constructor_overrides.update(overrides)
        self.config = resolve_config(config=config, constructor_overrides=constructor_overrides)
        self._ai_app = AIApp()

        @self._ai_app.ai_route("/ask", name="ask")
        def _default_ask(query: str) -> str:
            return f"Query received: {query}"

    @classmethod
    def from_env(cls) -> FastAI:
        """Create SDK instance using environment/profile/default resolution."""
        return cls()

    @classmethod
    def from_profile(cls, profile: str, **overrides: object) -> FastAI:
        """Create SDK instance from a profile plus explicit constructor overrides."""
        return cls(profile=profile, **cast(dict[str, Any], overrides))

    @classmethod
    def for_pgvector(
        cls,
        *,
        dsn: str,
        model: str,
        provider: str = "openai",
        provider_credential: str | None = None,
        **overrides: object,
    ) -> FastAI:
        """Create SDK instance preconfigured for pgvector backend."""
        extra = cast(dict[str, Any], overrides)
        return cls(
            vector_backend="pgvector",
            pgvector_dsn=dsn,
            model=model,
            provider=provider,
            provider_credential=provider_credential,
            **extra,
        )

    @classmethod
    def for_qdrant(
        cls,
        *,
        url: str,
        collection: str,
        model: str,
        provider: str = "openai",
        provider_credential: str | None = None,
        **overrides: object,
    ) -> FastAI:
        """Create SDK instance preconfigured for qdrant backend."""
        extra = cast(dict[str, Any], overrides)
        return cls(
            vector_backend="qdrant",
            qdrant_url=url,
            qdrant_collection=collection,
            model=model,
            provider=provider,
            provider_credential=provider_credential,
            **extra,
        )

    @classmethod
    def for_mongodb_atlas(
        cls,
        *,
        uri: str,
        database: str,
        collection: str,
        model: str,
        provider: str = "openai",
        provider_credential: str | None = None,
        **overrides: object,
    ) -> FastAI:
        """Create SDK instance preconfigured for MongoDB Atlas vector backend."""
        extra = cast(dict[str, Any], overrides)
        return cls(
            vector_backend="mongodb_atlas",
            mongodb_uri=uri,
            mongodb_database=database,
            mongodb_vector_collection=collection,
            model=model,
            provider=provider,
            provider_credential=provider_credential,
            **extra,
        )

    def ai_route(
        self,
        path: str | None = None,
        *,
        name: str | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register an AI route through the wrapped AIApp instance."""
        return self._ai_app.ai_route(path=path, name=name)

    def get_router(self) -> APIRouter:
        """Expose mountable router for plugin mode integration."""
        return self._ai_app.get_router()

    def mount(self, app: FastAPI, *, path: str = "/ai") -> None:
        """Mount FastAI routes into a host FastAPI app under a namespace path."""
        self._ai_app.include_in_app(app, prefix=path)

    def ask(self, query: str, *, debug: bool = False, route_name: str = "ask") -> dict[str, object]:
        """Synchronous library-style query helper."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            ask_response = asyncio.run(self.ask_async(query, debug=debug, route_name=route_name))
            return ask_response.model_dump()
        raise RuntimeError("FastAI.ask cannot be called inside an active event loop.")

    async def ask_async(
        self,
        query: str,
        *,
        debug: bool = False,
        route_name: str = "ask",
    ) -> AskResponse:
        """Async query helper using registered route handlers."""
        payload = AskRequest(query=query, debug=debug)
        return await self._ai_app.execute(route_name, payload)

    def add_data(self, path: str) -> None:
        """Forward ingestion placeholder call until ingestion pipeline is implemented."""
        self._ai_app.add_data(path)

    def summary(self) -> dict[str, object]:
        """Return resolved configuration as a serializable dictionary."""
        return {
            "runtime": self.config.runtime.__dict__,
            "vector_store": self.config.vector_store.__dict__,
            "retrieval": self.config.retrieval.__dict__,
            "ingestion": self.config.ingestion.__dict__,
            "llm": self.config.llm.__dict__,
            "auth": self.config.auth.__dict__,
        }


def mount_fastai_router(app: FastAPI, *, sdk: FastAI, path: str = "/ai") -> None:
    """Compatibility wrapper around the dedicated plugin mount entrypoint."""
    from .plugin import mount_fastai_router as plugin_mount_fastai_router

    plugin_mount_fastai_router(app, sdk=sdk, path=path)

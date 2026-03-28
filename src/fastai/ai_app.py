"""Public AIApp skeleton and route registration APIs."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import APIRouter, FastAPI

from .app.api.schemas import AskRequest, AskResponse
from .ingestion import discover_ingestion_files

HandlerReturn = str | AskResponse | dict[str, object]
RouteHandler = Callable[[str], HandlerReturn | Awaitable[HandlerReturn]]
LOGGER = logging.getLogger("fastai.ingestion")


@dataclass(frozen=True)
class RouteBinding:
    """Registered AI route metadata for runtime and introspection."""

    name: str
    path: str


class AIApp:
    """Developer-facing API surface for AI route registration and mounting."""

    def __init__(self) -> None:
        self._router = APIRouter()
        self._routes: dict[str, tuple[RouteBinding, RouteHandler]] = {}

    def ai_route(
        self,
        path: str | None = None,
        *,
        name: str | None = None,
    ) -> Callable[[RouteHandler], RouteHandler]:
        """Register an AI route and bind it to the internal API router."""

        def decorator(handler: RouteHandler) -> RouteHandler:
            route_name = name or handler.__name__
            route_path = path or f"/{route_name}"
            if not route_path.startswith("/"):
                raise ValueError("AI route path must start with '/'.")
            if route_name in self._routes:
                raise ValueError(f"AI route '{route_name}' is already registered.")

            async def endpoint(payload: AskRequest) -> AskResponse:
                return await self.execute(route_name, payload)

            self._router.add_api_route(
                route_path,
                endpoint,
                methods=["POST"],
                response_model=AskResponse,
                name=route_name,
                summary=f"AI route: {route_name}",
            )
            binding = RouteBinding(name=route_name, path=route_path)
            self._routes[route_name] = (binding, handler)
            return handler

        return decorator

    async def execute(self, route_name: str, payload: AskRequest) -> AskResponse:
        """Execute a registered AI route handler for library-style consumption."""
        if route_name not in self._routes:
            raise KeyError(f"AI route '{route_name}' is not registered.")
        _, handler = self._routes[route_name]
        result = handler(payload.query)
        if inspect.isawaitable(result):
            result = await result
        return self._to_ask_response(result)

    def get_router(self) -> APIRouter:
        """Return mountable router for plugin-mode host integration."""
        return self._router

    def include_in_app(self, app: FastAPI, *, prefix: str = "/ai") -> None:
        """Mount this AIApp's routes into an existing FastAPI app."""
        app.include_router(self._router, prefix=prefix)

    def registered_routes(self) -> tuple[RouteBinding, ...]:
        """Expose immutable list of registered route metadata."""
        return tuple(binding for binding, _ in self._routes.values())

    def add_data(self, path: str) -> None:
        """Validate and discover supported files for ingestion bootstrap."""
        discovered_files = discover_ingestion_files(path)
        LOGGER.info(
            "Ingestion discovery completed: %d supported file(s) found for path '%s'.",
            len(discovered_files),
            path,
        )

    @staticmethod
    def _to_ask_response(result: HandlerReturn) -> AskResponse:
        """Normalize handler return values to AskResponse."""
        if isinstance(result, AskResponse):
            return result
        if isinstance(result, str):
            return AskResponse(answer=result, sources=[])
        return AskResponse.model_validate(result)


def ai_route(
    app: AIApp,
    path: str | None = None,
    *,
    name: str | None = None,
) -> Callable[[RouteHandler], RouteHandler]:
    """Module-level helper mirroring AIApp.ai_route for ergonomic usage."""
    return app.ai_route(path=path, name=name)

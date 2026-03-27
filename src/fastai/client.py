"""Library integration client entrypoint for host application handlers."""

from __future__ import annotations

from typing import Any, cast

from .app.api.schemas import AskResponse
from .sdk import FastAI


class FastAIClient:
    """Small adapter for calling FastAI from existing host route handlers."""

    def __init__(self, sdk: FastAI) -> None:
        self._sdk = sdk

    def ask(self, query: str, *, debug: bool = False, route_name: str = "ask") -> dict[str, object]:
        """Execute a query through FastAI and return API-contract-compatible payload."""
        return self._sdk.ask(query=query, debug=debug, route_name=route_name)

    async def ask_async(
        self,
        query: str,
        *,
        debug: bool = False,
        route_name: str = "ask",
    ) -> AskResponse:
        """Async variant for frameworks/routes running in async contexts."""
        return await self._sdk.ask_async(query=query, debug=debug, route_name=route_name)


def create_fastai_client(sdk: FastAI | None = None, **sdk_kwargs: object) -> FastAIClient:
    """Create a library integration client from an SDK instance or SDK kwargs."""
    resolved_sdk = sdk or FastAI(**cast(dict[str, Any], sdk_kwargs))
    return FastAIClient(resolved_sdk)

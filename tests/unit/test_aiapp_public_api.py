from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastai import AIApp, ai_route
from fastai.app.api.schemas import AskRequest


def test_developer_route_registration_appears_in_openapi() -> None:
    ai_app = AIApp()

    @ai_app.ai_route("/support")
    def support_handler(query: str) -> str:
        return f"support: {query}"

    app = FastAPI()
    ai_app.include_in_app(app, prefix="")
    client = TestClient(app)

    response = client.post("/support", json={"query": "hello"})

    assert response.status_code == 200
    assert response.json()["answer"] == "support: hello"

    openapi = app.openapi()
    assert "/support" in openapi["paths"]
    assert openapi["paths"]["/support"]["post"]["operationId"].startswith("support_handler")


def test_module_level_ai_route_helper_registers_route() -> None:
    ai_app = AIApp()

    @ai_route(ai_app, "/faq")
    def faq_handler(query: str) -> dict[str, object]:
        return {"answer": f"faq: {query}", "sources": []}

    app = FastAPI()
    ai_app.include_in_app(app, prefix="")
    client = TestClient(app)

    response = client.post("/faq", json={"query": "billing"})

    assert response.status_code == 200
    assert response.json()["answer"] == "faq: billing"


def test_existing_host_routes_remain_usable_with_aiapp_plugin_mount() -> None:
    host_app = FastAPI()

    @host_app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    ai_app = AIApp()

    @ai_app.ai_route("/help", name="help_query")
    def help_handler(query: str) -> str:
        return f"help: {query}"

    ai_app.include_in_app(host_app, prefix="/ai")
    client = TestClient(host_app)

    host_response = client.get("/ping")
    ai_response = client.post("/ai/help", json={"query": "reset password"})

    assert host_response.status_code == 200
    assert host_response.json() == {"status": "ok"}
    assert ai_response.status_code == 200
    assert ai_response.json()["answer"] == "help: reset password"


def test_library_style_execution_uses_registered_handler() -> None:
    ai_app = AIApp()

    @ai_app.ai_route("/library", name="library_query")
    def library_handler(query: str) -> str:
        return f"library: {query}"

    async def _run() -> None:
        ask_response = await ai_app.execute("library_query", AskRequest(query="q"))
        assert ask_response.answer == "library: q"

    import asyncio

    asyncio.run(_run())


def test_add_data_placeholder_raises_clear_not_implemented_error() -> None:
    ai_app = AIApp()

    try:
        ai_app.add_data("docs/")
    except NotImplementedError as exc:
        assert "add_data is not implemented yet" in str(exc)
    else:
        raise AssertionError("Expected NotImplementedError")

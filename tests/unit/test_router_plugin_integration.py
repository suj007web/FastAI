from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastai import FastAI, get_fastai_router, mount_fastai_router


def test_host_app_can_mount_fastai_router_without_replacing_existing_routes() -> None:
    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    sdk = FastAI()
    mount_fastai_router(app, sdk=sdk, path="/ai")

    client = TestClient(app)
    ping_response = client.get("/ping")
    ask_response = client.post("/ai/ask", json={"query": "hello"})

    assert ping_response.status_code == 200
    assert ping_response.json() == {"status": "ok"}
    assert ask_response.status_code == 200



def test_mounted_route_returns_answer_and_sources_contract() -> None:
    app = FastAPI()
    sdk = FastAI()
    mount_fastai_router(app, sdk=sdk, path="/ai")

    client = TestClient(app)
    response = client.post("/ai/ask", json={"query": "refund"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Query received: refund"
    assert isinstance(payload["sources"], list)



def test_router_plugin_supports_configurable_mount_path() -> None:
    app = FastAPI()
    sdk = FastAI()

    app.include_router(get_fastai_router(sdk=sdk), prefix="/assistant")

    client = TestClient(app)
    response = client.post("/assistant/ask", json={"query": "support"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Query received: support"

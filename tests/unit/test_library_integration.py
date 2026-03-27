from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastai import FastAI, create_fastai_client, mount_fastai_router


def test_existing_host_route_calls_fastai_without_migration() -> None:
    app = FastAPI()
    sdk = FastAI()
    client = create_fastai_client(sdk)

    @app.post("/support/ask")
    def support_ask(payload: dict[str, object]) -> dict[str, object]:
        query = str(payload.get("query", ""))
        debug = bool(payload.get("debug", False))
        return client.ask(query=query, debug=debug)

    http = TestClient(app)
    response = http.post("/support/ask", json={"query": "refund policy", "debug": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Query received: refund policy"
    assert isinstance(payload["sources"], list)


def test_library_client_response_contract_matches_framework_route_shape() -> None:
    app = FastAPI()
    sdk = FastAI()
    client = create_fastai_client(sdk)
    mount_fastai_router(app, sdk=sdk, path="/ai")

    @app.post("/support/ask")
    def support_ask(payload: dict[str, object]) -> dict[str, object]:
        return client.ask(query=str(payload["query"]), debug=False)

    http = TestClient(app)
    library_response = http.post("/support/ask", json={"query": "billing"})
    framework_response = http.post("/ai/ask", json={"query": "billing"})

    assert library_response.status_code == 200
    assert framework_response.status_code == 200

    library_payload = library_response.json()
    framework_payload = framework_response.json()

    assert set(library_payload.keys()) == {"answer", "sources", "debug"}
    assert set(framework_payload.keys()) == {"answer", "sources", "debug"}
    assert library_payload["answer"] == framework_payload["answer"]
    assert isinstance(library_payload["sources"], list)

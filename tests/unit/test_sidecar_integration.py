from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastai.app import create_app
from fastai.app.api import router as api_router


class ProxyAskRequest(BaseModel):
    query: str
    debug: bool = False


def test_sidecar_service_is_callable_from_external_host_over_http() -> None:
    sidecar_app = create_app()
    sidecar_client = TestClient(sidecar_app)

    host_app = FastAPI()

    @host_app.post("/proxy/ask")
    def proxy_ask(payload: ProxyAskRequest) -> JSONResponse:
        upstream = sidecar_client.post(
            "/ask",
            json={"query": payload.query, "debug": payload.debug},
        )
        return JSONResponse(status_code=upstream.status_code, content=upstream.json())

    host_client = TestClient(host_app)
    response = host_client.post("/proxy/ask", json={"query": "refund policy", "debug": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Query received: refund policy"
    assert isinstance(payload["sources"], list)


def test_sidecar_success_response_matches_api_contract_shape() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post("/ask", json={"query": "hello"})

    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "sources" in payload
    assert isinstance(payload["answer"], str)
    assert isinstance(payload["sources"], list)


def test_sidecar_cross_service_error_mapping_is_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    sidecar_app = create_app()
    sidecar_client = TestClient(sidecar_app, raise_server_exceptions=False)

    host_app = FastAPI()

    @host_app.post("/proxy/ask")
    def proxy_ask(payload: dict[str, object]) -> JSONResponse:
        upstream = sidecar_client.post("/ask", json=payload)
        return JSONResponse(status_code=upstream.status_code, content=upstream.json())

    host_client = TestClient(host_app)

    invalid_response = host_client.post("/proxy/ask", json={})
    assert invalid_response.status_code == 400
    invalid_payload = invalid_response.json()
    assert invalid_payload["code"] == "invalid_request"
    assert invalid_payload["message"] == "Invalid request payload"
    assert isinstance(invalid_payload["request_id"], str)

    def failing_executor(payload: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(api_router, "_run_ask", failing_executor)

    internal_response = host_client.post("/proxy/ask", json={"query": "test"})
    assert internal_response.status_code == 500
    internal_payload = internal_response.json()
    assert internal_payload["code"] == "internal_error"
    assert internal_payload["message"] == "Internal server error"
    assert isinstance(internal_payload["request_id"], str)

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastai.app import create_app
from fastai.app.api import router as api_router
from fastai.app.api.schemas import IngestResponse


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


def test_sidecar_auth_mode_disabled_allows_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FASTAI_API_AUTH_MODE", "disabled")
    app = create_app()
    client = TestClient(app)

    response = client.post("/ask", json={"query": "hello"})

    assert response.status_code == 200


def test_sidecar_auth_mode_api_key_requires_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FASTAI_API_AUTH_MODE", "api_key")
    monkeypatch.setenv("FASTAI_API_KEY", "secret-key")

    app = create_app()
    client = TestClient(app)

    missing_header = client.post("/ask", json={"query": "hello"})
    assert missing_header.status_code == 401
    assert missing_header.json()["code"] == "unauthorized"

    wrong_key = client.post("/ask", headers={"X-API-Key": "wrong"}, json={"query": "hello"})
    assert wrong_key.status_code == 403
    assert wrong_key.json()["code"] == "forbidden"

    valid_key = client.post(
        "/ask",
        headers={"X-API-Key": "secret-key"},
        json={"query": "hello"},
    )
    assert valid_key.status_code == 200


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


def test_sidecar_ingest_endpoint_uses_default_docs_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_ingest(payload: object) -> IngestResponse:
        path = getattr(payload, "path", "")
        captured["path"] = str(path)
        return IngestResponse(
            status="ok",
            path=str(path),
            processed=1,
            skipped=0,
            failed=0,
            documents=1,
            chunks=1,
            embeddings=1,
        )

    monkeypatch.setattr(api_router, "_run_ingest", fake_ingest)

    app = create_app()
    client = TestClient(app)
    response = client.post("/ingest", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["path"] == "docs"
    assert captured["path"] == "docs"


def test_sidecar_ingest_endpoint_accepts_custom_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_ingest(payload: object) -> IngestResponse:
        path = getattr(payload, "path", "")
        captured["path"] = str(path)
        return IngestResponse(
            status="ok",
            path=str(path),
            processed=2,
            skipped=0,
            failed=0,
            documents=2,
            chunks=2,
            embeddings=2,
        )

    monkeypatch.setattr(api_router, "_run_ingest", fake_ingest)

    app = create_app()
    client = TestClient(app)
    response = client.post("/ingest", json={"path": "docs/manual"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["path"] == "docs/manual"
    assert captured["path"] == "docs/manual"


def test_sidecar_ingest_honors_api_key_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FASTAI_API_AUTH_MODE", "api_key")
    monkeypatch.setenv("FASTAI_API_KEY", "secret-key")

    app = create_app()
    client = TestClient(app)

    missing_header = client.post("/ingest", json={"path": "docs"})
    assert missing_header.status_code == 401
    assert missing_header.json()["code"] == "unauthorized"

    wrong_key = client.post("/ingest", headers={"X-API-Key": "wrong"}, json={"path": "docs"})
    assert wrong_key.status_code == 403
    assert wrong_key.json()["code"] == "forbidden"

    monkeypatch.setattr(
        api_router,
        "_run_ingest",
        lambda payload: IngestResponse(
            status="ok",
            path=getattr(payload, "path", "docs"),
            processed=0,
            skipped=0,
            failed=0,
            documents=0,
            chunks=0,
            embeddings=0,
        ),
    )
    valid_key = client.post(
        "/ingest",
        headers={"X-API-Key": "secret-key"},
        json={"path": "docs"},
    )
    assert valid_key.status_code == 200

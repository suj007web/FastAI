import pytest
from fastapi.testclient import TestClient

from fastai.app import AppSettings, create_app
from fastai.app.api import router as api_router


def test_create_app_returns_initialized_payload() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "fastai-framework", "status": "initialized"}


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_app_uses_explicit_settings() -> None:
    app = create_app(
        settings=AppSettings(env="test", host="127.0.0.1", port=9999, log_level="DEBUG")
    )
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "env": "test"}


def test_defaults_profile_uses_balanced_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FASTAI_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("FASTAI_LOG_LEVEL", raising=False)

    settings = AppSettings.from_env()

    assert settings.profile == "balanced"
    assert settings.log_level == "INFO"


def test_env_overrides_profile_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FASTAI_CONFIG_PROFILE", "dev")
    monkeypatch.setenv("FASTAI_LOG_LEVEL", "ERROR")

    settings = AppSettings.from_env()

    assert settings.profile == "dev"
    assert settings.log_level == "ERROR"
    assert "log_level" in settings.overridden_keys


def test_startup_config_summary_contains_effective_values() -> None:
    app = create_app(settings=AppSettings(profile="balanced", env="test", log_level="DEBUG"))

    with TestClient(app):
        summary = app.state.config_summary

    assert summary["effective"]["profile"] == "balanced"
    assert summary["effective"]["env"] == "test"
    assert isinstance(summary["overridden_keys"], list)


def test_invalid_payload_maps_to_400_error_shape() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post("/ask", json={})

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "invalid_request"
    assert payload["message"] == "Invalid request payload"
    assert isinstance(payload["request_id"], str)
    assert payload["request_id"]


def test_unhandled_error_maps_to_stable_500_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_executor(payload: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(api_router, "_run_ask", failing_executor)

    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/ask", json={"query": "hello"})

    assert response.status_code == 500
    payload = response.json()
    assert payload == {
        "code": "internal_error",
        "message": "Internal server error",
        "request_id": payload["request_id"],
    }
    assert isinstance(payload["request_id"], str)
    assert payload["request_id"]


def test_request_id_middleware_preserves_header() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post("/ask", headers={"X-Request-ID": "req-123"}, json={"query": "q"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"

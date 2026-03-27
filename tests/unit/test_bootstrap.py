import pytest
from fastapi.testclient import TestClient

from fastai.app import AppSettings, create_app


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

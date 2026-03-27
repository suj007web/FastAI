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

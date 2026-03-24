from fastapi.testclient import TestClient

from fastai.app import create_app


def test_create_app_returns_initialized_payload() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "fastai-framework", "status": "initialized"}

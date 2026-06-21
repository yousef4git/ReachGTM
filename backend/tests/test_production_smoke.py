from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_smoke(monkeypatch):
    async def fake_init_pool():
        return None

    async def fake_close_pool():
        return None

    monkeypatch.setattr("backend.app.main.init_pool", fake_init_pool)
    monkeypatch.setattr("backend.app.main.close_pool", fake_close_pool)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"service": "backend", "status": "ok"}
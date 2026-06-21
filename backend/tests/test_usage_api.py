from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.usage import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_usage_summary_endpoint():
    response = client.get("/usage/summary")

    assert response.status_code == 200

    data = response.json()

    assert "metrics" in data
    assert "total_usage" in data
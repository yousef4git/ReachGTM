from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.analytics import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_strategy_performance_endpoint():
    response = client.post(
        "/analytics/strategy-performance",
        json={
            "sent": 100,
            "opened": 40,
            "replied": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["open_rate"] == 0.4
    assert data["reply_rate"] == 0.1
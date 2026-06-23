from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.app.api.content as content_api


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(content_api.router, prefix="/api/v1")
    return app


def test_generate_content_api():
    client = TestClient(_make_app())

    response = client.post(
        "/api/v1/content/generate",
        json={
            "content_types": ["cold_email", "linkedin_post"],
            "count_per_type": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 4
    assert len(data["assets"]) == 4
    assert data["assets"][0]["type"] == "cold_email"
    assert data["assets"][0]["title"]
    assert data["assets"][0]["body"]


def test_list_content_api_returns_empty_list():
    client = TestClient(_make_app())

    response = client.get("/api/v1/content/")

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "assets": [],
    }
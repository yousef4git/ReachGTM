"""Tests for long-term company memory service + API (Epic 4 — Phase 2).

DB-free: the asyncpg connection is faked for the service tests, and the get_db
dependency is overridden for the API tests. Deterministic.
"""
import json
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.services import memory_service
from backend.app.db.connection import get_db
from backend.app.middleware.tenant import TenantMiddleware
from backend.app.services.auth_service import create_access_token
import backend.app.api.memory as memory_api


# ── Fake asyncpg connection ──────────────────────────────────────────────────

class FakeConn:
    def __init__(self, *, fetchval=None, fetch=None, execute="INSERT 0 1"):
        self._fetchval = fetchval
        self._fetch = fetch or []
        self._execute = execute
        self.calls: list[tuple] = []

    async def execute(self, sql, *args):
        self.calls.append(("execute", sql, args))
        return self._execute

    async def fetchval(self, sql, *args):
        self.calls.append(("fetchval", sql, args))
        return self._fetchval

    async def fetch(self, sql, *args):
        self.calls.append(("fetch", sql, args))
        return self._fetch


COMPANY = "11111111-1111-1111-1111-111111111111"


# ── service ──────────────────────────────────────────────────────────────────

class TestMemoryService:
    @pytest.mark.asyncio
    async def test_remember_upserts_with_json_value(self):
        conn = FakeConn()
        await memory_service.remember(conn, COMPANY, "icp", {"title": "VP Sales"})
        kind, sql, args = conn.calls[0]
        assert kind == "execute"
        assert "INSERT INTO company_memory" in sql and "ON CONFLICT" in sql
        assert args[0] == uuid.UUID(COMPANY)
        assert args[1] == "icp"
        assert json.loads(args[2]) == {"title": "VP Sales"}  # value json-encoded

    @pytest.mark.asyncio
    async def test_recall_decodes_jsonb_string(self):
        conn = FakeConn(fetchval='{"title": "VP Sales"}')
        assert await memory_service.recall(conn, COMPANY, "icp") == {"title": "VP Sales"}

    @pytest.mark.asyncio
    async def test_recall_missing_returns_none(self):
        conn = FakeConn(fetchval=None)
        assert await memory_service.recall(conn, COMPANY, "nope") is None

    @pytest.mark.asyncio
    async def test_recall_all_builds_dict(self):
        conn = FakeConn(fetch=[
            {"key": "icp", "value": '{"x": 1}'},
            {"key": "tone", "value": '"friendly"'},
        ])
        assert await memory_service.recall_all(conn, COMPANY) == {
            "icp": {"x": 1},
            "tone": "friendly",
        }

    @pytest.mark.asyncio
    async def test_forget_reports_deletion(self):
        assert await memory_service.forget(FakeConn(execute="DELETE 1"), COMPANY, "k") is True
        assert await memory_service.forget(FakeConn(execute="DELETE 0"), COMPANY, "k") is False


# ── API ──────────────────────────────────────────────────────────────────────

def _make_app(fake_conn: FakeConn) -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantMiddleware)
    app.include_router(memory_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: fake_conn
    return app


def _auth_header() -> dict:
    token = create_access_token(uuid.uuid4(), uuid.UUID(COMPANY), "owner")
    return {"Authorization": f"Bearer {token}"}


class TestMemoryApi:
    def test_requires_auth(self):
        client = TestClient(_make_app(FakeConn()))
        assert client.get("/api/v1/memory/").status_code == 401

    def test_put_then_returns_value(self):
        client = TestClient(_make_app(FakeConn()))
        resp = client.put(
            "/api/v1/memory/icp",
            json={"value": {"title": "VP Sales"}},
            headers=_auth_header(),
        )
        assert resp.status_code == 200
        assert resp.json() == {"key": "icp", "value": {"title": "VP Sales"}}

    def test_get_missing_is_404(self):
        client = TestClient(_make_app(FakeConn(fetchval=None)))
        resp = client.get("/api/v1/memory/nope", headers=_auth_header())
        assert resp.status_code == 404

    def test_list_returns_all(self):
        conn = FakeConn(fetch=[{"key": "tone", "value": '"friendly"'}])
        resp = TestClient(_make_app(conn)).get("/api/v1/memory/", headers=_auth_header())
        assert resp.status_code == 200
        assert resp.json() == {"tone": "friendly"}

    def test_delete_reports_deleted(self):
        conn = FakeConn(execute="DELETE 1")
        resp = TestClient(_make_app(conn)).delete("/api/v1/memory/icp", headers=_auth_header())
        assert resp.status_code == 200
        assert resp.json() == {"key": "icp", "deleted": True}

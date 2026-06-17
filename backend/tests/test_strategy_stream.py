"""Tests for the SSE streaming endpoint and relay (PR #14).

Network-free: the agents service boundary is faked (httpx) for the relay, and
the relay itself is stubbed for the endpoint/auth tests. Deterministic.
"""
import uuid

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.app.services.agent_stream as agent_stream
from backend.app.services.agent_stream import stream_strategy_events
import backend.app.api.strategy as strategy_api
from backend.app.middleware.tenant import TenantMiddleware
from backend.app.services.auth_service import create_access_token


# ── Fake agents-service HTTP stream ──────────────────────────────────────────

class _FakeResponse:
    def __init__(self, chunks: list[bytes], status: int = 200):
        self._chunks = chunks
        self.status_code = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("bad status", request=None, response=None)

    async def aiter_bytes(self):
        for chunk in self._chunks:
            yield chunk


class _FakeClient:
    """Stand-in for httpx.AsyncClient with a scripted stream."""
    chunks: list[bytes] = []
    raise_on_stream: Exception | None = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def stream(self, method, url, **kwargs):
        if _FakeClient.raise_on_stream is not None:
            raise _FakeClient.raise_on_stream
        return _FakeResponse(_FakeClient.chunks)


async def _collect(agen) -> str:
    out = ""
    async for frame in agen:
        out += frame
    return out


def _last_event(sse_text: str) -> str:
    events = [ln[len("event: "):] for ln in sse_text.splitlines() if ln.startswith("event: ")]
    return events[-1] if events else ""


# ── Relay service ────────────────────────────────────────────────────────────

class TestRelay:
    @pytest.mark.asyncio
    async def test_relays_agent_frames_in_order_ending_in_done(self, monkeypatch):
        _FakeClient.raise_on_stream = None
        _FakeClient.chunks = [
            b"event: agent_start\ndata: {}\n\n",
            b"event: agent_progress\ndata: {\"agent\": \"research\"}\n\n",
            b"event: done\ndata: {}\n\n",
        ]
        monkeypatch.setattr(agent_stream.httpx, "AsyncClient", _FakeClient)

        out = await _collect(stream_strategy_events(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(), goal="launch product",
        ))

        assert out.index("agent_start") < out.index("agent_progress") < out.index("event: done")
        assert _last_event(out) == "done"  # terminal frame is done
        assert "event: error" not in out

    @pytest.mark.asyncio
    async def test_emits_error_then_done_when_agents_unreachable(self, monkeypatch):
        _FakeClient.raise_on_stream = httpx.ConnectError("connection refused")
        monkeypatch.setattr(agent_stream.httpx, "AsyncClient", _FakeClient)

        out = await _collect(stream_strategy_events(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(), goal="launch product",
        ))

        assert "event: error" in out
        assert out.index("event: error") < out.index("event: done")
        assert _last_event(out) == "done"  # terminal done
        # reset shared state for other tests
        _FakeClient.raise_on_stream = None


# ── Endpoint + auth ──────────────────────────────────────────────────────────

def _make_app() -> FastAPI:
    """Minimal app: tenant middleware + strategy router, no DB lifespan."""
    app = FastAPI()
    app.add_middleware(TenantMiddleware)
    app.include_router(strategy_api.router, prefix="/api/v1")
    return app


class TestEndpoint:
    def test_requires_auth(self):
        client = TestClient(_make_app())
        resp = client.post("/api/v1/strategy/generate/stream", json={"goal": "x"})
        assert resp.status_code == 401

    def test_authenticated_stream_is_ordered_and_terminates(self, monkeypatch):
        async def _fake_stream(**kwargs):
            yield "event: agent_start\ndata: {}\n\n"
            yield "event: agent_progress\ndata: {}\n\n"
            yield "event: agent_complete\ndata: {}\n\n"
            yield "event: done\ndata: {}\n\n"

        monkeypatch.setattr(strategy_api, "stream_strategy_events", _fake_stream)

        token = create_access_token(uuid.uuid4(), uuid.uuid4(), "owner")
        client = TestClient(_make_app())
        resp = client.post(
            "/api/v1/strategy/generate/stream",
            json={"goal": "Launch our analytics product"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.text
        assert body.index("agent_start") < body.index("agent_complete") < body.index("event: done")

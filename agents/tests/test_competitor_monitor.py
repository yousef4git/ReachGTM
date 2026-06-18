"""Tests for competitor monitoring (Epic 4 — Phase 2).

Deterministic and network-free: the cadence gate is pure; the Perplexity MCP
boundary is mocked.
"""
from datetime import datetime, timedelta, timezone

import pytest

import agents.app.tools.competitor_monitor as cm
from shared.schemas import Signal


# ── cadence gate ─────────────────────────────────────────────────────────────

class TestIsRefreshDue:
    def test_never_run_is_due(self):
        assert cm.is_refresh_due(None) is True

    def test_recent_run_not_due(self):
        now = datetime(2026, 6, 18, tzinfo=timezone.utc)
        last = now - timedelta(days=3)
        assert cm.is_refresh_due(last, now) is False

    def test_old_run_is_due(self):
        now = datetime(2026, 6, 18, tzinfo=timezone.utc)
        last = now - timedelta(days=8)
        assert cm.is_refresh_due(last, now) is True

    def test_exactly_interval_is_due(self):
        now = datetime(2026, 6, 18, tzinfo=timezone.utc)
        last = now - timedelta(days=7)
        assert cm.is_refresh_due(last, now) is True

    def test_naive_last_run_is_handled(self):
        now = datetime(2026, 6, 18, tzinfo=timezone.utc)
        last = datetime(2026, 6, 1)  # naive -> treated as UTC
        assert cm.is_refresh_due(last, now) is True


# ── refresh via Perplexity (mocked) ──────────────────────────────────────────

class _FakeTool:
    def __init__(self, result):
        self.name = "perplexity_search"
        self._result = result
        self.calls = []

    async def ainvoke(self, args):
        self.calls.append(args)
        return self._result


class TestRefreshCompetitorSignals:
    @pytest.mark.asyncio
    async def test_empty_competitors_returns_empty(self, monkeypatch):
        assert await cm.refresh_competitor_signals([]) == []

    @pytest.mark.asyncio
    async def test_no_mcp_returns_empty(self, monkeypatch):
        async def _none(server):
            return []

        monkeypatch.setattr(cm, "get_mcp_tools", _none, raising=False)
        # patch the late-imported symbol path too
        import agents.app.tools.mcp_client as mcp_client
        monkeypatch.setattr(mcp_client, "get_mcp_tools", _none)
        assert await cm.refresh_competitor_signals(["Acme"]) == []

    @pytest.mark.asyncio
    async def test_builds_one_signal_per_competitor(self, monkeypatch):
        import agents.app.tools.mcp_client as mcp_client

        async def _tools(server):
            return [_FakeTool("Raised a $20M Series B")]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        signals = await cm.refresh_competitor_signals(["Acme", "Globex"])
        assert len(signals) == 2
        assert all(isinstance(s, Signal) for s in signals)
        assert signals[0].type == "competitor_update"
        assert "Acme" in signals[0].description
        assert "Globex" in signals[1].description

    @pytest.mark.asyncio
    async def test_per_competitor_error_becomes_error_signal(self, monkeypatch):
        import agents.app.tools.mcp_client as mcp_client

        class _BadTool:
            name = "perplexity"

            async def ainvoke(self, args):
                raise RuntimeError("boom")

        async def _tools(server):
            return [_BadTool()]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        signals = await cm.refresh_competitor_signals(["Acme"])
        assert len(signals) == 1
        assert signals[0].type == "error"


# ── monitor combiner ─────────────────────────────────────────────────────────

class TestMonitorCompetitors:
    @pytest.mark.asyncio
    async def test_skips_when_not_due(self, monkeypatch):
        called = False

        async def _should_not_run(competitors):
            nonlocal called
            called = True
            return []

        monkeypatch.setattr(cm, "refresh_competitor_signals", _should_not_run)
        now = datetime(2026, 6, 18, tzinfo=timezone.utc)
        out = await cm.monitor_competitors(["Acme"], last_run=now - timedelta(days=1), now=now)
        assert out == {"refreshed": False, "signals": []}
        assert called is False

    @pytest.mark.asyncio
    async def test_refreshes_when_due(self, monkeypatch):
        async def _signals(competitors):
            return [Signal(type="competitor_update", description="x", relevance="y")]

        monkeypatch.setattr(cm, "refresh_competitor_signals", _signals)
        out = await cm.monitor_competitors(["Acme"], last_run=None)
        assert out["refreshed"] is True
        assert len(out["signals"]) == 1

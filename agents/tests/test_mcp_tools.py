"""Tests for MCP server registry + research tool wiring (PR #24).

Deterministic and network-free: server selection is driven by config, and the
MCP client / tools are mocked. No live MCP servers are contacted.
"""
import pytest

import agents.app.tools.mcp_client as mcp_client
from agents.app.config import settings
from agents.app.graph.nodes import research


# ── server registry gating ───────────────────────────────────────────────────

class TestServerConfigs:
    def test_only_fetch_when_nothing_else_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "perplexity_api_key", "")
        monkeypatch.setattr(settings, "databar_api_key", "")
        monkeypatch.setattr(settings, "databar_mcp_url", "")
        monkeypatch.setattr(settings, "fetch_mcp_enabled", True)
        assert set(mcp_client._server_configs()) == {"fetch"}

    def test_perplexity_enabled_by_key(self, monkeypatch):
        monkeypatch.setattr(settings, "perplexity_api_key", "pk")
        monkeypatch.setattr(settings, "databar_api_key", "")
        monkeypatch.setattr(settings, "fetch_mcp_enabled", False)
        cfg = mcp_client._server_configs()
        assert set(cfg) == {"perplexity"}
        assert cfg["perplexity"]["headers"]["Authorization"] == "Bearer pk"

    def test_databar_needs_both_key_and_url(self, monkeypatch):
        monkeypatch.setattr(settings, "perplexity_api_key", "")
        monkeypatch.setattr(settings, "fetch_mcp_enabled", False)
        # key only -> not enabled
        monkeypatch.setattr(settings, "databar_api_key", "dk")
        monkeypatch.setattr(settings, "databar_mcp_url", "")
        assert "databar" not in mcp_client._server_configs()
        # key + url -> enabled
        monkeypatch.setattr(settings, "databar_mcp_url", "https://databar.example/mcp")
        assert "databar" in mcp_client._server_configs()


# ── get_mcp_tools is fail-safe ───────────────────────────────────────────────

class TestGetMcpTools:
    @pytest.mark.asyncio
    async def test_unconfigured_server_returns_empty(self, monkeypatch):
        monkeypatch.setattr(settings, "databar_api_key", "")
        monkeypatch.setattr(settings, "databar_mcp_url", "")
        # no network attempted because there's no config for 'databar'
        assert await mcp_client.get_mcp_tools("databar") == []

    @pytest.mark.asyncio
    async def test_client_error_is_swallowed(self, monkeypatch):
        monkeypatch.setattr(settings, "fetch_mcp_enabled", True)

        class _Boom:
            def __init__(self, *a, **k):
                raise RuntimeError("cannot start fetch server")

        monkeypatch.setattr(mcp_client, "MultiServerMCPClient", _Boom)
        assert await mcp_client.get_mcp_tools("fetch") == []


# ── research helpers ─────────────────────────────────────────────────────────

class _FakeTool:
    def __init__(self, name, result):
        self.name = name
        self._result = result

    async def ainvoke(self, args):
        self._args = args
        return self._result


class TestResearchHelpers:
    @pytest.mark.asyncio
    async def test_databar_enrich_returns_tool_output(self, monkeypatch):
        async def _tools(server):
            assert server == "databar"
            return [_FakeTool("databar_enrich_company", "ACME: 200 employees")]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        out = await research._run_databar_enrich("ACME")
        assert out == ["ACME: 200 employees"]

    @pytest.mark.asyncio
    async def test_fetch_url_returns_empty_when_unconfigured(self, monkeypatch):
        async def _none(server):
            return []

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _none)
        assert await research._run_fetch_url("https://x.com") == []

    @pytest.mark.asyncio
    async def test_helper_swallows_tool_errors(self, monkeypatch):
        class _BadTool:
            name = "fetch"

            async def ainvoke(self, args):
                raise RuntimeError("boom")

        async def _tools(server):
            return [_BadTool()]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        out = await research._run_fetch_url("https://x.com")
        assert out == ["fetch_error:RuntimeError"]

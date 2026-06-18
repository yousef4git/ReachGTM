"""Tests for Attio CRM ICP enrichment (Epic 4 — Phase 2).

Network-free: the Attio MCP boundary is mocked. Deterministic.
"""
import pytest

import agents.app.tools.mcp_client as mcp_client
from agents.app.config import settings
from agents.app.tools.attio_enrich import enrich_icp_from_attio, _merge_icp
from shared.schemas import ICPProfile


def _icp(**over) -> ICPProfile:
    base = dict(
        title="VP Sales",
        industry="B2B SaaS",
        company_size="Unknown",
        budget_range="Unknown",
        pain_points=["low reply rates"],
        goals=["hit pipeline"],
        buying_committee=["VP Sales"],
        disqualifiers=["no sales team"],
    )
    base.update(over)
    return ICPProfile(**base)


# ── server registry ──────────────────────────────────────────────────────────

def test_attio_registered_only_with_key_and_url(monkeypatch):
    monkeypatch.setattr(settings, "perplexity_api_key", "")
    monkeypatch.setattr(settings, "databar_api_key", "")
    monkeypatch.setattr(settings, "fetch_mcp_enabled", False)
    monkeypatch.setattr(settings, "attio_api_key", "k")
    monkeypatch.setattr(settings, "attio_mcp_url", "")
    assert "attio" not in mcp_client._server_configs()
    monkeypatch.setattr(settings, "attio_mcp_url", "https://attio.example/mcp")
    assert "attio" in mcp_client._server_configs()


# ── _merge_icp ───────────────────────────────────────────────────────────────

class TestMergeIcp:
    def test_unions_list_fields(self):
        merged = _merge_icp(_icp(), {"buying_committee": ["VP Sales", "CFO", "RevOps"]})
        assert merged.buying_committee == ["VP Sales", "CFO", "RevOps"]  # deduped + appended

    def test_backfills_empty_scalars_only(self):
        merged = _merge_icp(_icp(), {"company_size": "200-500", "budget_range": "$50k"})
        assert merged.company_size == "200-500"
        assert merged.budget_range == "$50k"

    def test_does_not_overwrite_known_scalar(self):
        icp = _icp(company_size="50-100")
        merged = _merge_icp(icp, {"company_size": "9999"})
        assert merged.company_size == "50-100"  # already known -> unchanged

    def test_no_changes_returns_same_object(self):
        icp = _icp()
        assert _merge_icp(icp, {}) is icp


# ── enrich_icp_from_attio ────────────────────────────────────────────────────

class _Tool:
    def __init__(self, name, result):
        self.name = name
        self._result = result

    async def ainvoke(self, args):
        return self._result


class TestEnrichIcpFromAttio:
    @pytest.mark.asyncio
    async def test_no_attio_returns_same_icp(self, monkeypatch):
        async def _none(server):
            return []

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _none)
        icp = _icp()
        assert await enrich_icp_from_attio(icp) is icp

    @pytest.mark.asyncio
    async def test_merges_enrichment_payload(self, monkeypatch):
        async def _tools(server):
            assert server == "attio"
            return [_Tool("attio_enrich_icp", {"buying_committee": ["CFO"], "company_size": "200-500"})]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        out = await enrich_icp_from_attio(_icp())
        assert "CFO" in out.buying_committee
        assert out.company_size == "200-500"

    @pytest.mark.asyncio
    async def test_tool_error_returns_original(self, monkeypatch):
        class _BadTool:
            name = "attio"

            async def ainvoke(self, args):
                raise RuntimeError("boom")

        async def _tools(server):
            return [_BadTool()]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        icp = _icp()
        assert await enrich_icp_from_attio(icp) is icp

    @pytest.mark.asyncio
    async def test_non_dict_result_returns_original(self, monkeypatch):
        async def _tools(server):
            return [_Tool("attio", "not a dict")]

        monkeypatch.setattr(mcp_client, "get_mcp_tools", _tools)
        icp = _icp()
        assert await enrich_icp_from_attio(icp) is icp

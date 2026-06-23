"""Tests for Multi-ICP mode (Epic 4 — Phase 2).

Deterministic: content_node is forced down the template path (no network) by
clearing the OpenAI key.
"""
import uuid

import pytest

from shared.schemas import ICPProfile
from agents.app.graph.state import GTMState
from agents.app.config import settings
from agents.app.graph.nodes.content import (
    content_node,
    _resolve_target_icps,
    _ctx_for_icp,
    _strategy_context,
    MAX_ICPS,
)


def _icp(title: str, industry: str = "B2B SaaS") -> dict:
    return {
        "title": title,
        "industry": industry,
        "company_size": "50-200 employees",
        "budget_range": "$10k-$50k",
        "pain_points": ["p1", "p2", "p3", "p4"],
        "goals": ["g1"],
        "buying_committee": ["VP"],
        "disqualifiers": ["none"],
    }


# ── _resolve_target_icps ─────────────────────────────────────────────────────

class TestResolveTargetIcps:
    def test_none_when_no_strategy_and_no_extras(self):
        state = GTMState(company_id=uuid.uuid4(), user_id=uuid.uuid4())
        assert _resolve_target_icps(state) == []

    def test_collects_additional_icps_from_metadata(self):
        state = GTMState(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(),
            metadata={"additional_icps": [_icp("Founder"), _icp("RevOps Lead")]},
        )
        icps = _resolve_target_icps(state)
        assert [i.title for i in icps] == ["Founder", "RevOps Lead"]

    def test_dedupes_by_title_and_caps_at_max(self):
        state = GTMState(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(),
            metadata={"additional_icps": [
                _icp("A"), _icp("A"), _icp("B"), _icp("C"), _icp("D"),
            ]},
        )
        titles = [i.title for i in _resolve_target_icps(state)]
        assert titles == ["A", "B", "C"]  # deduped + capped at MAX_ICPS
        assert len(titles) == MAX_ICPS

    def test_skips_malformed_entries(self):
        state = GTMState(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(),
            metadata={"additional_icps": [{"bad": "shape"}, _icp("Valid")]},
        )
        assert [i.title for i in _resolve_target_icps(state)] == ["Valid"]


# ── _ctx_for_icp ─────────────────────────────────────────────────────────────

def test_ctx_for_icp_overrides_icp_fields():
    base = _strategy_context(None)
    icp = ICPProfile(**_icp("CFO", industry="Fintech"))
    ctx = _ctx_for_icp(base, icp)
    assert ctx["industry"] == "Fintech"
    assert ctx["icp_title"] == "CFO"
    assert ctx["pain_points"] == ["p1", "p2", "p3"]  # capped at 3
    # non-ICP fields preserved from base
    assert ctx["value_headline"] == base["value_headline"]


# ── content_node multi-ICP ───────────────────────────────────────────────────

class TestContentNodeMultiIcp:
    @pytest.mark.asyncio
    async def test_generates_per_icp(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_api_key", "")  # force template path
        state = GTMState(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(),
            metadata={
                "content_types": ["cold_email"],
                "count_per_type": 1,
                "additional_icps": [_icp("Founder"), _icp("RevOps Lead")],
            },
        )
        result = await content_node(state)
        # 2 ICPs x 1 asset
        assert len(result.content_assets) == 2
        assert sorted(a.target_icp for a in result.content_assets) == ["Founder", "RevOps Lead"]

    @pytest.mark.asyncio
    async def test_single_icp_unchanged(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_api_key", "")
        state = GTMState(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email"], "count_per_type": 1},
        )
        result = await content_node(state)
        assert len(result.content_assets) == 1  # no multi-ICP fan-out

    @pytest.mark.asyncio
    async def test_multi_icp_combines_with_ab_variants(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_api_key", "")
        state = GTMState(
            company_id=uuid.uuid4(), user_id=uuid.uuid4(),
            metadata={
                "content_types": ["cold_email"],
                "count_per_type": 1,
                "additional_icps": [_icp("Founder"), _icp("RevOps Lead")],
                "ab_variants": True,
            },
        )
        result = await content_node(state)
        # 2 ICPs x 1 asset x 3 variants
        assert len(result.content_assets) == 6

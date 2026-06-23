"""Tests for A/B variant generation (Epic 4 — Phase 2).

Deterministic, no LLM: variant generation is pure; the content_node integration
forces the template path so it doesn't hit the network.
"""
import uuid

import pytest

from shared.schemas import ContentAsset, ContentType
from agents.app.graph.state import GTMState
from agents.app.config import settings
from agents.app.graph.nodes.content import content_node
from agents.app.graph.nodes.variants import (
    make_variants,
    expand_assets_to_variants,
    VARIANT_STRATEGIES,
    NUM_VARIANTS,
)


def _asset() -> ContentAsset:
    return ContentAsset(
        type=ContentType.COLD_EMAIL,
        title="Cut your sales cycle in half",
        body="Hi there, here's how teams like yours close faster.",
        target_icp="B2B SaaS",
    )


# ── make_variants ────────────────────────────────────────────────────────────

class TestMakeVariants:
    def test_returns_three_variants(self):
        assert len(make_variants(_asset())) == NUM_VARIANTS == 3

    def test_titles_are_labelled_abc(self):
        titles = [v.title for v in make_variants(_asset())]
        assert titles == [
            "[Variant A] Cut your sales cycle in half",
            "[Variant B] Cut your sales cycle in half",
            "[Variant C] Cut your sales cycle in half",
        ]

    def test_bodies_are_distinct_and_contain_base(self):
        base = _asset()
        variants = make_variants(base)
        bodies = [v.body for v in variants]
        assert len(set(bodies)) == 3  # all different
        for v in variants:
            assert base.body in v.body  # base copy preserved in each

    def test_each_variant_uses_its_strategy_hook_and_cta(self):
        variants = make_variants(_asset())
        for label, v in zip(VARIANT_STRATEGIES, variants):
            assert v.body.startswith(VARIANT_STRATEGIES[label]["hook"])
            assert v.body.rstrip().endswith(VARIANT_STRATEGIES[label]["cta"])

    def test_preserves_type_and_icp_and_unique_ids(self):
        base = _asset()
        variants = make_variants(base)
        assert all(v.type == base.type for v in variants)
        assert all(v.target_icp == base.target_icp for v in variants)
        assert len({v.id for v in variants}) == 3  # fresh ids


# ── expand_assets_to_variants ────────────────────────────────────────────────

def test_expand_multiplies_by_three():
    assets = [_asset(), _asset()]
    expanded = expand_assets_to_variants(assets)
    assert len(expanded) == 6


# ── content_node integration ─────────────────────────────────────────────────

class TestContentNodeABFlag:
    @pytest.mark.asyncio
    async def test_flag_on_yields_three_variants_per_asset(self, monkeypatch):
        # Force the deterministic template path (no network).
        monkeypatch.setattr(settings, "openai_api_key", "")
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email"], "count_per_type": 1, "ab_variants": True},
        )
        result = await content_node(state)
        assert len(result.content_assets) == 3
        labels = sorted(a.title.split("]")[0] for a in result.content_assets)
        assert labels == ["[Variant A", "[Variant B", "[Variant C"]

    @pytest.mark.asyncio
    async def test_flag_off_leaves_count_unchanged(self, monkeypatch):
        monkeypatch.setattr(settings, "openai_api_key", "")
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email"], "count_per_type": 1},
        )
        result = await content_node(state)
        assert len(result.content_assets) == 1
        assert "[Variant" not in result.content_assets[0].title

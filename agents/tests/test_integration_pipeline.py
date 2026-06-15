"""End-to-end integration test for the GTM graph (PR #20 / issue #19).

Proves the assembled research -> strategy -> content -> brand_alignment
pipeline runs end to end and produces a schema-valid state, with the external
boundaries (Perplexity MCP and the OpenAI LLM) stubbed so the run is
deterministic and network-free.

NOTE: true record/replay HTTP cassettes are a follow-up — they require a VCR
dependency and recorded fixtures against live MCP/LLM endpoints, which aren't
wired yet. Until then this test exercises the full graph via the nodes'
built-in offline fallbacks.
"""

import uuid

import pytest

import agents.app.tools.mcp_client as mcp_client
from agents.app.config import settings
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState
from shared.schemas import ContentAsset, ResearchReport, ValidationStatus


@pytest.fixture
def offline(monkeypatch):
    """Force both external boundaries into their deterministic offline paths."""

    async def _no_tools(*args, **kwargs):
        return []

    monkeypatch.setattr(mcp_client, "get_mcp_tools", _no_tools)
    # Empty key makes the content node use its ColdIQ template fallback.
    monkeypatch.setattr(settings, "openai_api_key", "")


@pytest.mark.asyncio
async def test_full_pipeline_runs_end_to_end(offline):
    # Goal is passed via metadata: passing it through `messages` currently
    # breaks state coercion (add_messages reducer -> Message objects the base
    # schema rejects). Tracked as a follow-up bug.
    state = GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        metadata={
            "goal": "Launch our B2B SaaS analytics product",
            "content_types": ["cold_email", "linkedin_post"],
            "count_per_type": 2,
        },
    )

    result = await graph.ainvoke(state.model_dump())

    # Pipeline ran all the way to the final node.
    assert result["current_agent"] == "brand_alignment"

    # Research stage produced a schema-valid report.
    report = result["research_report"]
    assert isinstance(report, ResearchReport)
    assert report.company_profile.name

    # Content stage produced assets.
    assets = result["content_assets"]
    assert len(assets) > 0
    assert all(isinstance(a, ContentAsset) for a in assets)


@pytest.mark.asyncio
async def test_pipeline_brand_scores_every_asset(offline):
    state = GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        metadata={"content_types": ["cold_email"], "count_per_type": 2},
    )

    result = await graph.ainvoke(state.model_dump())
    assets = result["content_assets"]

    assert len(assets) > 0
    for asset in assets:
        # Brand alignment node ran on every asset (epic acceptance criterion:
        # brand alignment score > 0.0 on all content assets).
        assert asset.brand_alignment_score is not None
        assert asset.brand_alignment_score > 0.0
        assert asset.validation_status in (
            ValidationStatus.APPROVED,
            ValidationStatus.REVISED,
            ValidationStatus.REJECTED,
        )

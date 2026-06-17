import uuid

import pytest

from agents.app.graph.nodes.strategy import strategy_node
from agents.app.graph.state import GTMState
from shared.schemas import (
    CompanyProfile,
    Competitor,
    GTMStrategy,
    ICPProfile,
    MarketSize,
    ResearchReport,
    Segment,
    Signal,
)


def _research() -> ResearchReport:
    return ResearchReport(
        company_profile=CompanyProfile(
            name="Acme Analytics",
            industry="B2B SaaS",
            stage="seed",
            description="Product analytics for PLG teams",
        ),
        market_size=MarketSize(tam="10B", sam="1B", som="50M", source="x", year=2026),
        competitors=[
            Competitor(
                name="Mixpanel",
                positioning="Product analytics",
                strengths=["brand", "integrations"],
                weaknesses=["pricing", "complexity"],
            ),
            Competitor(
                name="Amplitude",
                positioning="Digital analytics",
                strengths=["enterprise"],
                weaknesses=["onboarding"],
            ),
        ],
        segments=[
            Segment(
                name="PLG SaaS",
                description="self-serve SaaS",
                size_estimate="5000 companies",
                pain_points=["no insight into activation"],
                buying_triggers=["new PLG motion"],
            )
        ],
        icp=ICPProfile(
            title="Head of Growth",
            industry="B2B SaaS",
            company_size="50-200 employees",
            budget_range="$20k-$80k",
            pain_points=["slow activation", "blind to funnel drop-off"],
            goals=["improve activation", "data-driven roadmap"],
            buying_committee=["Head of Growth", "CTO"],
            disqualifiers=["no product telemetry"],
        ),
        signals=[Signal(type="hiring", description="hiring growth eng", relevance="high")],
        sources=["src"],
    )


def _state(**kwargs) -> GTMState:
    return GTMState(company_id=uuid.uuid4(), user_id=uuid.uuid4(), **kwargs)


@pytest.mark.asyncio
async def test_strategy_node_sets_strategy_and_agent():
    result = await strategy_node(_state(research_report=_research()))
    assert result.current_agent == "strategy"
    assert isinstance(result.gtm_strategy, GTMStrategy)


@pytest.mark.asyncio
async def test_strategy_carries_research_icp():
    research = _research()
    result = await strategy_node(_state(research_report=research))
    assert result.gtm_strategy.icp.title == research.icp.title
    assert result.gtm_strategy.icp.industry == research.icp.industry


@pytest.mark.asyncio
async def test_strategy_builds_a_battlecard_per_competitor():
    research = _research()
    result = await strategy_node(_state(research_report=research))
    names = {b.competitor for b in result.gtm_strategy.battlecards}
    assert names == {c.name for c in research.competitors}


@pytest.mark.asyncio
async def test_strategy_has_channels_and_positioning():
    result = await strategy_node(_state(research_report=_research()))
    strategy = result.gtm_strategy
    assert len(strategy.channels) >= 1
    assert all(c.priority >= 1 for c in strategy.channels)
    assert strategy.positioning_statement.strip()
    assert len(strategy.ninety_day_plan) >= 1


@pytest.mark.asyncio
async def test_strategy_without_research_report_is_graceful():
    # research node normally runs first, but the node must not crash if it didn't.
    result = await strategy_node(_state())
    assert isinstance(result.gtm_strategy, GTMStrategy)

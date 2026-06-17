import uuid

import pytest

from agents.app.graph.nodes.orchestrator import decide_route, orchestrator_node
from agents.app.graph.state import GTMState
from shared.schemas import (
    Channel,
    CompanyProfile,
    Competitor,
    GTMMotion,
    GTMStrategy,
    ICPProfile,
    MarketSize,
    ResearchReport,
    Segment,
    Signal,
    ValueProp,
)


def _min_icp() -> ICPProfile:
    return ICPProfile(
        title="Growth Lead",
        industry="B2B SaaS",
        company_size="10-200",
        budget_range="$10k-$50k",
        pain_points=["slow GTM"],
        goals=["launch faster"],
        buying_committee=["Founder"],
        disqualifiers=["no GTM motion"],
    )


def _min_research() -> ResearchReport:
    return ResearchReport(
        company_profile=CompanyProfile(
            name="Acme", industry="B2B SaaS", stage="seed", description="x"
        ),
        market_size=MarketSize(tam="1", sam="1", som="1", source="s", year=2026),
        competitors=[
            Competitor(name="C", positioning="p", strengths=["s"], weaknesses=["w"])
        ],
        segments=[
            Segment(
                name="S",
                description="d",
                size_estimate="1",
                pain_points=["p"],
                buying_triggers=["t"],
            )
        ],
        icp=_min_icp(),
        signals=[Signal(type="t", description="d", relevance="r")],
        sources=["src"],
    )


def _min_strategy() -> GTMStrategy:
    return GTMStrategy(
        motion=GTMMotion.SLG,
        icp=_min_icp(),
        value_proposition=ValueProp(
            headline="h", subheadline="s", proof_points=["p"], differentiators=["d"]
        ),
        channels=[Channel(name="cold_email", priority=1, rationale="r", kpis=["k"])],
        battlecards=[],
        growth_loops=[],
        ninety_day_plan=[],
        positioning_statement="pos",
    )


def _state(**kwargs) -> GTMState:
    return GTMState(company_id=uuid.uuid4(), user_id=uuid.uuid4(), **kwargs)


# ── decide_route ─────────────────────────────────────────────────────────────

def test_decide_route_research_on_fresh_state():
    assert decide_route(_state()) == "research"


def test_decide_route_strategy_when_research_done():
    assert decide_route(_state(research_report=_min_research())) == "strategy"


def test_decide_route_content_when_strategy_exists():
    state = _state(research_report=_min_research(), gtm_strategy=_min_strategy())
    assert decide_route(state) == "content"


# ── orchestrator_node ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_sets_agent_and_route():
    result = await orchestrator_node(_state())
    assert result.current_agent == "orchestrator"
    assert result.metadata["route"] == "research"


@pytest.mark.asyncio
async def test_orchestrator_extracts_goal_from_last_message():
    state = _state(messages=[{"role": "user", "content": "Launch our API product"}])
    result = await orchestrator_node(state)
    assert result.metadata["goal"] == "Launch our API product"


# ── graph wiring ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_graph_skips_research_when_report_already_present():
    """When research is already done, the graph routes straight to strategy,
    so the existing ResearchReport is preserved (research node never runs)."""
    from agents.app.graph.graph import graph

    report = _min_research()
    report.sources = ["PRESERVED_MARKER"]
    state = _state(research_report=report)

    result = await graph.ainvoke(state.model_dump())

    assert result["research_report"].sources == ["PRESERVED_MARKER"]

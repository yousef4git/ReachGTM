"""
Strategy Node — GTM Framework Generation (PR #11 / issue #15)

Turns the ResearchReport in state into a complete, schema-valid GTMStrategy:
ICP, value proposition, GTM motion, channel mix, competitive battlecards,
growth loops, and a 90-day plan.

The build is deterministic and derived from the research report (reusing the
merged pm-skills tools for positioning and value proposition), so the node is
fully testable offline. LLM-based enrichment of the narrative fields is a
follow-up; the schema-valid structure is produced here without a network call.
"""

from __future__ import annotations

from typing import Optional

from agents.app.graph.state import GTMState
from agents.app.tools.skills.pm_skills import positioning_statement, value_proposition
from shared.schemas import (
    Channel,
    CompetitiveBattlecard,
    Competitor,
    GrowthLoop,
    GTMMotion,
    GTMStrategy,
    ICPProfile,
    Milestone,
    ResearchReport,
    ValueProp,
)

_DEFAULT_ICP = ICPProfile(
    title="Growth or Marketing Lead",
    industry="B2B SaaS",
    company_size="10-200 employees",
    budget_range="Unknown",
    pain_points=["Manual GTM research", "Inconsistent positioning"],
    goals=["Launch campaigns faster", "Improve messaging consistency"],
    buying_committee=["Founder", "Marketing Manager"],
    disqualifiers=["No active GTM motion"],
)


def _choose_motion(report: Optional[ResearchReport]) -> GTMMotion:
    """Pick a GTM motion from company stage (deterministic heuristic)."""
    if report is None:
        return GTMMotion.SLG
    stage = report.company_profile.stage.lower()
    if stage in ("pre-seed", "seed"):
        return GTMMotion.PLG
    if stage in ("series a", "series-a", "growth"):
        return GTMMotion.SLG
    return GTMMotion.MLG


def _build_value_proposition(icp: ICPProfile, company_name: str) -> ValueProp:
    result = value_proposition.invoke(
        {
            "headline": f"{company_name}: {icp.goals[0] if icp.goals else 'Win your market faster'}",
            "target_customer": f"{icp.title} at {icp.industry} companies",
            "key_benefit": icp.goals[0] if icp.goals else "accelerate go-to-market",
            "proof_points": [
                "Built on proven GTM frameworks",
                f"Tailored to {icp.industry}",
                "Faster time-to-launch",
            ],
            "differentiators": [
                "End-to-end research → strategy → content pipeline",
                "Brand-aligned, ICP-targeted output",
            ],
        }
    )
    return ValueProp(**result)


def _build_positioning(icp: ICPProfile, company_name: str, top_competitor: str) -> str:
    result = positioning_statement.invoke(
        {
            "product_name": company_name,
            "target_customer": f"{icp.title}s",
            "need": (icp.pain_points[0] if icp.pain_points else "need faster GTM execution"),
            "market_category": f"{icp.industry} GTM platform",
            "key_benefit": (icp.goals[0] if icp.goals else "ships GTM strategy in hours, not weeks"),
            "primary_competitor": top_competitor,
            "primary_differentiation": "automates the full research-to-content pipeline",
        }
    )
    return result["statement"]


def _build_channels(motion: GTMMotion) -> list[Channel]:
    base = [
        Channel(
            name="cold_email",
            priority=1,
            rationale="Direct, measurable outbound to the ICP buying committee.",
            kpis=["reply_rate", "meetings_booked"],
            estimated_cac="$150-$400",
        ),
        Channel(
            name="linkedin",
            priority=2,
            rationale="Build credibility and warm the ICP before outreach.",
            kpis=["engagement_rate", "connection_accept_rate"],
            estimated_cac="$100-$300",
        ),
        Channel(
            name="content",
            priority=3,
            rationale="Compounding inbound that supports every other channel.",
            kpis=["organic_traffic", "content_sourced_pipeline"],
            estimated_cac="$50-$200",
        ),
    ]
    # PLG leans on content first; SLG/MLG lead with outbound.
    if motion == GTMMotion.PLG:
        base[0].priority, base[2].priority = 3, 1
    return base


def _build_battlecards(
    competitors: list[Competitor], company_name: str
) -> list[CompetitiveBattlecard]:
    cards: list[CompetitiveBattlecard] = []
    for comp in competitors:
        cards.append(
            CompetitiveBattlecard(
                competitor=comp.name,
                our_strengths_vs_them=[
                    f"Faster end-to-end GTM than {comp.name}",
                    *[f"Address their gap: {w}" for w in comp.weaknesses[:2]],
                ],
                their_strengths_vs_us=comp.strengths[:3] or ["Established presence"],
                winning_moves=[
                    f"Lead with speed and {company_name}'s integrated pipeline",
                    "Anchor on ICP pain points they underserve",
                ],
                losing_scenarios=[
                    f"Buyer already standardized on {comp.name}",
                ],
                talk_track=(
                    f"{comp.name} is strong on "
                    f"{(comp.strengths[0] if comp.strengths else 'brand')}, "
                    f"but {company_name} wins on speed and an integrated "
                    "research-to-content workflow."
                ),
            )
        )
    return cards


def _build_growth_loops() -> list[GrowthLoop]:
    return [
        GrowthLoop(
            name="Content flywheel",
            type="content",
            description="Published GTM assets drive organic traffic that converts to trials.",
            input_metric="assets_published",
            output_metric="organic_signups",
        ),
        GrowthLoop(
            name="Outbound-to-referral",
            type="sales",
            description="Closed customers refer peers in the same ICP segment.",
            input_metric="customers_won",
            output_metric="referral_meetings",
        ),
    ]


def _build_plan(company_name: str) -> list[Milestone]:
    return [
        Milestone(
            week=2,
            goal="Validate ICP and positioning with 10 discovery calls",
            kpis=["calls_completed", "icp_fit_score"],
            owner="Founder",
        ),
        Milestone(
            week=6,
            goal="Launch outbound + content engine across top channels",
            kpis=["meetings_booked", "reply_rate"],
            owner="Growth Lead",
        ),
        Milestone(
            week=12,
            goal=f"Reach repeatable pipeline for {company_name}",
            kpis=["qualified_pipeline", "cac"],
            owner="Growth Lead",
        ),
    ]


async def strategy_node(state: GTMState) -> GTMState:
    """Build a complete GTMStrategy from the research report in state."""
    report = state.research_report
    icp = report.icp if report is not None else _DEFAULT_ICP
    company_name = report.company_profile.name if report is not None else "the company"
    competitors = report.competitors if report is not None else []
    top_competitor = competitors[0].name if competitors else "the incumbent"

    motion = _choose_motion(report)

    strategy = GTMStrategy(
        motion=motion,
        icp=icp,
        value_proposition=_build_value_proposition(icp, company_name),
        channels=_build_channels(motion),
        battlecards=_build_battlecards(competitors, company_name),
        growth_loops=_build_growth_loops(),
        ninety_day_plan=_build_plan(company_name),
        positioning_statement=_build_positioning(icp, company_name, top_competitor),
    )

    return state.model_copy(
        update={
            "current_agent": "strategy",
            "gtm_strategy": strategy,
        }
    )

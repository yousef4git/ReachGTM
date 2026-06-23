"""Tests for the content LangGraph node (PR #12)."""
import uuid
import pytest

from shared.schemas import (
    ContentType, GTMStrategy, GTMMotion, ICPProfile,
    ValueProp, Channel, CompetitiveBattlecard, GrowthLoop, Milestone,
    ValidationStatus,
)
from agents.app.graph.state import GTMState
from agents.app.graph.nodes.content import (
    _strategy_context,
    _ctx_formatted,
    _build_llm_prompt,
    content_node,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_strategy() -> GTMStrategy:
    return GTMStrategy(
        motion=GTMMotion.SLG,
        icp=ICPProfile(
            title="VP of Sales",
            industry="B2B SaaS",
            company_size="200-500",
            budget_range="$50k-$100k",
            pain_points=["low lead quality", "long sales cycles", "poor forecast accuracy"],
            goals=["increase pipeline by 40%", "reduce time-to-close"],
            buying_committee=["VP Sales", "CRO", "RevOps Director"],
            disqualifiers=["under 50 employees", "no dedicated SDR team"],
        ),
        value_proposition=ValueProp(
            headline="AI-powered lead scoring that doubles conversion rates",
            subheadline="Stop wasting your SDR team on unqualified leads",
            proof_points=["2.1x conversion improvement", "40% reduction in sales cycle"],
            differentiators=["proprietary intent data", "native CRM integration"],
        ),
        channels=[
            Channel(name="cold_email", priority=1, rationale="Direct reach to ICP", kpis=["reply_rate"]),
            Channel(name="linkedin", priority=2, rationale="Social proof and engagement", kpis=["engagement_rate"]),
        ],
        battlecards=[
            CompetitiveBattlecard(
                competitor="Acme",
                our_strengths_vs_them=["better intent data"],
                their_strengths_vs_us=["brand recognition"],
                winning_moves=["compare data accuracy"],
                losing_scenarios=["price competition"],
                talk_track="Acme is great for enterprises, but our data accuracy is 3x better.",
            ),
        ],
        growth_loops=[
            GrowthLoop(name="VC to portfolio", type="sales", description="Partner with VC firms", input_metric="partnerships", output_metric="warm intros"),
        ],
        ninety_day_plan=[
            Milestone(week=1, goal="Define ICP", kpis=["ICP doc"], owner="Bader"),
        ],
        positioning_statement="For B2B sales leaders who need accurate pipeline data, ReachGTM is the AI-powered lead scoring platform that doubles conversion rates without increasing team headcount.",
    )


@pytest.fixture
def empty_state() -> GTMState:
    return GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )


# ── Strategy Context ─────────────────────────────────────────────────────────

class TestStrategyContext:
    def test_with_strategy(self, sample_strategy):
        ctx = _strategy_context(sample_strategy)
        assert ctx["industry"] == "B2B SaaS"
        assert ctx["icp_title"] == "VP of Sales"
        assert "AI-powered" in ctx["value_headline"]
        assert "cold_email" in ctx["top_channels"]
        assert ctx["motion"] == "sales_led_growth"

    def test_with_none(self):
        ctx = _strategy_context(None)
        assert ctx["industry"] == "B2B SaaS"
        assert ctx["icp_title"] == "Mid-market decision maker"
        assert len(ctx["pain_points"]) == 2


class TestCtxFormatted:
    def test_formats_dict_to_string(self):
        ctx = _strategy_context(None)
        result = _ctx_formatted(ctx)
        assert "Company industry: B2B SaaS" in result
        assert "GTM motion:" in result
        assert "Positioning:" in result


# ── LLM Prompt Builders ──────────────────────────────────────────────────────

class TestBuildLlmPrompt:
    def test_cold_email_prompt_has_rules(self):
        messages = _build_llm_prompt(ContentType.COLD_EMAIL, "context", 1)
        assert len(messages) == 2
        assert "ColdIQ" in messages[0].content
        assert "pattern-interrupt" in messages[1].content
        assert "50 characters" in messages[1].content

    def test_linkedin_prompt_has_hook(self):
        messages = _build_llm_prompt(ContentType.LINKEDIN_POST, "context", 1)
        assert "Hook" in messages[1].content
        assert "paragraphs" in messages[1].content

    def test_blog_outline_prompt(self):
        messages = _build_llm_prompt(ContentType.BLOG_OUTLINE, "context", 2)
        assert "blog outline" in messages[1].content.lower()
        assert "meta description" in messages[1].content

    def test_ad_copy_prompt(self):
        messages = _build_llm_prompt(ContentType.AD_COPY, "context", 3)
        assert "ad copy" in messages[1].content.lower()
        assert "Headline" in messages[1].content


# ── Template Fallback (no LLM) ───────────────────────────────────────────────

class TestTemplateFallback:
    @pytest.mark.asyncio
    async def test_returns_content_assets_default_types(self, empty_state):
        result = await content_node(empty_state)
        assert result.current_agent == "content"
        assert len(result.content_assets) > 0

    @pytest.mark.asyncio
    async def test_respects_metadata_content_types(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email"], "count_per_type": 2},
        )
        result = await content_node(state)
        assert len(result.content_assets) == 2
        assert all(a.type == ContentType.COLD_EMAIL for a in result.content_assets)

    @pytest.mark.asyncio
    async def test_respects_count_per_type(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["linkedin_post"], "count_per_type": 4},
        )
        result = await content_node(state)
        assert len(result.content_assets) == 4

    @pytest.mark.asyncio
    async def test_generates_cold_email_via_templates(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email"], "count_per_type": 1},
        )
        result = await content_node(state)
        asset = result.content_assets[0]
        assert asset.type == ContentType.COLD_EMAIL
        assert len(asset.title) > 0
        assert len(asset.body) > 0

    @pytest.mark.asyncio
    async def test_generates_linkedin_post_via_templates(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["linkedin_post"], "count_per_type": 1},
        )
        result = await content_node(state)
        asset = result.content_assets[0]
        assert asset.type == ContentType.LINKEDIN_POST
        assert len(asset.body) > 0
        assert "hook" in asset.__dict__ or len(asset.body) > 50

    @pytest.mark.asyncio
    async def test_uses_strategy_context_when_provided(self, empty_state, sample_strategy):
        state = empty_state.model_copy(update={"gtm_strategy": sample_strategy})
        result = await content_node(state)
        assert len(result.content_assets) > 0

    @pytest.mark.asyncio
    async def test_all_assets_have_required_fields(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email", "linkedin_post"], "count_per_type": 2},
        )
        result = await content_node(state)
        for asset in result.content_assets:
            assert asset.id is not None
            assert asset.type in (ContentType.COLD_EMAIL, ContentType.LINKEDIN_POST)
            assert len(asset.title) > 0
            assert len(asset.body) > 0
            assert asset.validation_status == ValidationStatus.PENDING

    @pytest.mark.asyncio
    async def test_unknown_content_types_are_skipped(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": ["cold_email", "nonexistent_type"], "count_per_type": 1},
        )
        result = await content_node(state)
        # Should only generate the valid type
        assert len(result.content_assets) == 1
        assert result.content_assets[0].type == ContentType.COLD_EMAIL

    @pytest.mark.asyncio
    async def test_empty_types_defaults_to_both(self):
        state = GTMState(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            metadata={"content_types": [], "count_per_type": 1},
        )
        result = await content_node(state)
        types_found = {a.type for a in result.content_assets}
        assert ContentType.COLD_EMAIL in types_found
        assert ContentType.LINKEDIN_POST in types_found

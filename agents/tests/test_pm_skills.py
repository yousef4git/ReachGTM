"""Tests for pm-skills tool wrappers — ICP & positioning (PR #15).

Deterministic unit tests: no live LLM/network calls. Tools that promise
schema-valid output are checked by re-parsing the result through the
corresponding shared.schemas model.
"""
from shared.schemas import ICPProfile, ValueProp
from agents.app.tools.skills.pm_skills import (
    build_icp_profile,
    score_icp_fit,
    positioning_statement,
    value_proposition,
    PM_SKILLS,
    BUYING_COMMITTEE_BY_TIER,
    FIT_WEIGHTS,
    _company_size_tier,
)


# ── build_icp_profile ────────────────────────────────────────────────────────

class TestBuildIcpProfile:
    BASE = {
        "title": "VP of Sales",
        "industry": "B2B SaaS",
        "company_size": "50-200 employees",
        "budget_range": "$10k-$50k / yr",
        "pain_points": ["low reply rates", "long ramp time"],
        "goals": ["hit pipeline targets", "shorten sales cycle"],
    }

    def test_output_is_schema_valid(self):
        result = build_icp_profile.invoke(dict(self.BASE))
        # Must round-trip through the schema without error.
        profile = ICPProfile(**result)
        assert profile.title == "VP of Sales"
        assert profile.industry == "B2B SaaS"

    def test_derives_buying_committee_from_size(self):
        result = build_icp_profile.invoke(dict(self.BASE))
        # "50-200 employees" -> ceiling 200 -> mid_market tier
        assert result["buying_committee"] == BUYING_COMMITTEE_BY_TIER["mid_market"]

    def test_applies_default_disqualifiers(self):
        result = build_icp_profile.invoke(dict(self.BASE))
        assert result["disqualifiers"]
        assert "No executive sponsor identified" in result["disqualifiers"]

    def test_respects_explicit_committee_and_disqualifiers(self):
        result = build_icp_profile.invoke({
            **self.BASE,
            "buying_committee": ["Champion", "Economic Buyer"],
            "disqualifiers": ["Wrong region"],
        })
        assert result["buying_committee"] == ["Champion", "Economic Buyer"]
        assert result["disqualifiers"] == ["Wrong region"]

    def test_enterprise_size_gets_enterprise_committee(self):
        result = build_icp_profile.invoke({**self.BASE, "company_size": "5000+ employees"})
        assert result["buying_committee"] == BUYING_COMMITTEE_BY_TIER["enterprise"]


# ── score_icp_fit ────────────────────────────────────────────────────────────

class TestScoreIcpFit:
    ICP = {
        "title": "VP of Sales",
        "industry": "B2B SaaS",
        "company_size": "50-200 employees",
        "budget_range": "$10k-$50k / yr",
        "pain_points": ["low reply rates"],
        "goals": ["hit pipeline targets"],
        "buying_committee": ["VP Sales"],
        "disqualifiers": ["No sales team"],
    }

    def test_perfect_match_is_tier_a(self):
        result = score_icp_fit.invoke({
            "icp": dict(self.ICP),
            "account_industry": "B2B SaaS",
            "account_size": "120 employees",
            "account_budget": "$30k / yr",
            "account_signals": ["Series A raised"],
        })
        assert result["score"] == 100
        assert result["tier"] == "A"
        assert result["gaps"] == []

    def test_industry_mismatch_loses_full_industry_weight(self):
        result = score_icp_fit.invoke({
            "icp": dict(self.ICP),
            "account_industry": "Healthcare",
            "account_size": "120 employees",
            "account_budget": "$30k / yr",
            "account_signals": ["Series A raised"],
        })
        assert result["score"] == 100 - FIT_WEIGHTS["industry"]
        assert any("Industry" in g for g in result["gaps"])

    def test_score_always_in_range_and_tiering(self):
        worst = score_icp_fit.invoke({
            "icp": dict(self.ICP),
            "account_industry": "Logistics",
            "account_size": "9000 employees",
        })
        assert 0 <= worst["score"] <= 100
        assert worst["tier"] == "C"

    def test_partial_industry_match_gets_half_weight(self):
        result = score_icp_fit.invoke({
            "icp": dict(self.ICP),
            "account_industry": "SaaS",  # substring of "B2B SaaS"
            "account_size": "120 employees",
        })
        # half industry + full size, no budget, no signals
        assert result["score"] == FIT_WEIGHTS["industry"] // 2 + FIT_WEIGHTS["size"]


# ── positioning_statement ────────────────────────────────────────────────────

class TestPositioningStatement:
    ARGS = {
        "product_name": "ReachGTM",
        "target_customer": "early-stage B2B founders",
        "need": "need a GTM strategy fast",
        "market_category": "AI GTM platform",
        "key_benefit": "turns research into a ready-to-run plan in minutes",
        "primary_competitor": "hiring a consultant",
        "primary_differentiation": "delivers it in minutes, not weeks",
    }

    def test_statement_follows_moore_template(self):
        result = positioning_statement.invoke(dict(self.ARGS))
        s = result["statement"]
        assert s.startswith("For early-stage B2B founders who need a GTM strategy fast,")
        # "AI ..." starts with a vowel -> "an", not "a"
        assert "ReachGTM is an AI GTM platform that" in s
        assert "Unlike hiring a consultant, ReachGTM delivers it in minutes" in s

    def test_components_echo_inputs(self):
        result = positioning_statement.invoke(dict(self.ARGS))
        assert result["components"]["product_name"] == "ReachGTM"
        assert result["components"]["primary_competitor"] == "hiring a consultant"

    def test_statement_is_a_plain_string(self):
        result = positioning_statement.invoke(dict(self.ARGS))
        # ready to drop into GTMStrategy.positioning_statement
        assert isinstance(result["statement"], str)

    def test_consonant_category_uses_a(self):
        result = positioning_statement.invoke({**self.ARGS, "market_category": "CRM"})
        assert "ReachGTM is a CRM that" in result["statement"]


# ── value_proposition ────────────────────────────────────────────────────────

class TestValueProposition:
    ARGS = {
        "headline": "Your GTM strategy, generated",
        "target_customer": "seed-stage founders",
        "key_benefit": "launch faster",
        "proof_points": ["3-week MVP", "used by 4 design partners"],
        "differentiators": ["multi-agent pipeline", "research-grounded"],
    }

    def test_output_is_schema_valid(self):
        result = value_proposition.invoke(dict(self.ARGS))
        prop = ValueProp(**result)
        assert prop.headline == "Your GTM strategy, generated"
        assert prop.proof_points == ["3-week MVP", "used by 4 design partners"]

    def test_derives_subheadline_when_omitted(self):
        result = value_proposition.invoke(dict(self.ARGS))
        assert result["subheadline"] == "Built for seed-stage founders — launch faster."

    def test_respects_explicit_subheadline(self):
        result = value_proposition.invoke({**self.ARGS, "subheadline": "Custom line."})
        assert result["subheadline"] == "Custom line."


# ── Helpers ──────────────────────────────────────────────────────────────────

class TestCompanySizeTier:
    def test_tiers(self):
        assert _company_size_tier("10-50 employees") == "smb"
        assert _company_size_tier("50-200 employees") == "mid_market"
        assert _company_size_tier("1000+") == "mid_market"
        assert _company_size_tier("5,000 employees") == "enterprise"

    def test_no_number_defaults_mid_market(self):
        assert _company_size_tier("enterprise-grade") == "mid_market"


# ── Registry ─────────────────────────────────────────────────────────────────

class TestRegistry:
    def test_contains_4_tools(self):
        assert len(PM_SKILLS) == 4

    def test_tool_names(self):
        names = {t.name for t in PM_SKILLS}
        assert names == {
            "build_icp_profile",
            "score_icp_fit",
            "positioning_statement",
            "value_proposition",
        }

    def test_all_tools_have_descriptions(self):
        for tool in PM_SKILLS:
            assert tool.description, f"{tool.name} has no description"

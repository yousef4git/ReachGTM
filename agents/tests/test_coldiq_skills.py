"""Tests for ColdIQ tool wrappers (PR #16)."""
from agents.app.tools.skills.coldiq_skills import (
    sales_triggers,
    cold_email_sequence,
    linkedin_post,
    score_coldiq_compliance,
    COLDIQ_SKILLS,
    SALES_TRIGGERS,
    COLD_EMAIL_TEMPLATES,
    LINKEDIN_HOOK_FORMATS,
)


# ── Sales Triggers ──────────────────────────────────────────────────────────

class TestSalesTriggers:
    def test_returns_all_categories_when_no_filter(self):
        result = sales_triggers.invoke({})
        # 7 categories — hiring(10) + funding(10) + product_launch(10)
        # + leadership_change(10) + regulatory(5) + competitive(5) + customer_behavior(5) = 55
        assert len(result) == 55
        assert all("trigger" in t and "signal" in t for t in result)

    def test_filters_by_single_category(self):
        result = sales_triggers.invoke({"trigger_types": ["hiring"]})
        assert len(result) == 10
        assert result[0]["trigger"] == "VP / Director of Sales hired"

    def test_filters_by_multiple_categories(self):
        result = sales_triggers.invoke({"trigger_types": ["funding", "regulatory"]})
        assert len(result) == 15  # 10 funding + 5 regulatory

    def test_returns_empty_for_unknown_category(self):
        result = sales_triggers.invoke({"trigger_types": ["nonexistent"]})
        assert result == []

    def test_all_categories_have_entries(self):
        for category, triggers in SALES_TRIGGERS.items():
            assert len(triggers) >= 5, f"{category} has fewer than 5 triggers"
            for t in triggers:
                assert "trigger" in t
                assert "signal" in t


# ── Cold Email Sequence ─────────────────────────────────────────────────────

class TestColdEmailSequence:
    def test_returns_3_emails(self):
        result = cold_email_sequence.invoke({
            "target_name": "Ahmed",
            "target_title": "VP Marketing",
            "company_name": "TechCo",
            "industry": "SaaS",
            "pain_points": ["low reply rates", "bad lead quality"],
            "social_proof": "Helped SimilarCo increase reply rates by 40%",
        })
        assert len(result) == 3

    def test_correct_sequence_positions(self):
        result = cold_email_sequence.invoke({
            "target_name": "Sara",
            "target_title": "CEO",
            "company_name": "GrowthInc",
            "industry": "Fintech",
            "pain_points": ["slow sales cycles"],
            "social_proof": "Reduced cycle time by 30% for a fintech peer",
        })
        assert result[0]["sequence_position"] == 1
        assert result[1]["sequence_position"] == 2
        assert result[2]["sequence_position"] == 3

    def test_includes_target_name_in_body(self):
        result = cold_email_sequence.invoke({
            "target_name": "Khalid",
            "target_title": "CTO",
            "company_name": "DataFlow",
            "industry": "AI",
            "pain_points": ["data silos"],
            "social_proof": "Unified 5 data sources for an AI startup",
        })
        assert "Khalid" in result[0]["body"]
        assert "Khalid" in result[1]["body"]
        assert "Khalid" in result[2]["body"]

    def test_subject_lines_under_50_chars(self):
        result = cold_email_sequence.invoke({
            "target_name": "Lama",
            "target_title": "Head of Sales",
            "company_name": "CloudKit",
            "industry": "DevTools",
            "pain_points": ["long ramp times"],
            "social_proof": "Cut ramp from 6 to 3 weeks for a devtools company",
        })
        for email in result:
            assert len(email["subject"]) <= 50, f"Subject too long: '{email['subject']}'"

    def test_email_1_has_soft_cta_not_demo(self):
        result = cold_email_sequence.invoke({
            "target_name": "Nora",
            "target_title": "CMO",
            "company_name": "BrandLab",
            "industry": "Marketing",
            "pain_points": ["low MQL to SQL conversion"],
            "social_proof": "Improved conversion 2x for a marketing agency",
        })
        body = result[0]["body"].lower()
        assert "demo" not in body
        assert "call" not in body or "curious" in body

    def test_email_3_is_direct_ask(self):
        result = cold_email_sequence.invoke({
            "target_name": "Fahad",
            "target_title": "VP Growth",
            "company_name": "ScaleUp",
            "industry": "E-commerce",
            "pain_points": ["high churn"],
            "social_proof": "Reduced churn 25% for an e-commerce platform",
        })
        body = result[2]["body"].lower()
        assert "minutes" in body or "call" in body

    def test_uses_trigger_in_email_1(self):
        result = cold_email_sequence.invoke({
            "target_name": "Mona",
            "target_title": "Head of Revenue",
            "company_name": "RevMax",
            "industry": "SaaS",
            "pain_points": ["flat pipeline"],
            "social_proof": "Filled pipeline 3x for a SaaS company",
            "triggers": ["Series A raised ($5M+)"],
        })
        assert "series" in result[0]["body"].lower()


# ── LinkedIn Post ───────────────────────────────────────────────────────────

class TestLinkedInPost:
    def test_returns_expected_keys(self):
        result = linkedin_post.invoke({
            "topic": "cold outreach at scale",
            "target_audience": "SaaS founders",
        })
        assert "hook" in result
        assert "body_paragraphs" in result
        assert "cta" in result
        assert "post" in result
        assert "tone" in result

    def test_has_3_body_paragraphs(self):
        result = linkedin_post.invoke({
            "topic": "sales automation",
            "target_audience": "B2B marketers",
            "tone": "contrarian",
        })
        assert len(result["body_paragraphs"]) == 3

    def test_hook_mentions_target_audience_and_topic(self):
        result = linkedin_post.invoke({
            "topic": "ICP definition",
            "target_audience": "early-stage founders",
        })
        assert "early-stage founders" in result["hook"]
        assert "ICP definition" in result["hook"] or "icp" in result["hook"].lower()

    def test_cta_is_engagement_based(self):
        result = linkedin_post.invoke({
            "topic": "cold email",
            "target_audience": "SDRs",
            "tone": "professional",
        })
        assert "comment" in result["cta"].lower() or "agree" in result["cta"].lower()

    def test_post_includes_all_parts(self):
        result = linkedin_post.invoke({
            "topic": "GTM strategy",
            "target_audience": "startup CEOs",
        })
        full = result["post"]
        assert result["hook"] in full
        assert result["cta"] in full
        for p in result["body_paragraphs"]:
            assert p in full


# ── Compliance Scoring ──────────────────────────────────────────────────────

class TestScoreColdiqCompliance:
    def test_good_cold_email_scores_high(self):
        result = score_coldiq_compliance.invoke({
            "content_type": "cold_email",
            "subject": "Quick thought on outreach",
            "body": "Hi Ahmed,\n\nNoticed you hired a new VP Sales.\n\nOne thing I see often: low reply rates despite volume.\n\nWe helped SimilarCo fix this.\n\nCurious if this resonates.\n\nBest,\nMe",
        })
        assert result["score"] >= 6
        assert "no_spam_triggers" in result["passing_rules"]
        assert "subject_line_under_50" in result["passing_rules"]

    def test_spammy_email_scores_low(self):
        result = score_coldiq_compliance.invoke({
            "content_type": "cold_email",
            "subject": "FREE limited time offer act now!!!",
            "body": "This guaranteed offer is exclusive for you. Limited time only.",
        })
        assert result["score"] <= 4
        assert "no_spam_triggers" in result["failing_rules"]

    def test_good_linkedin_post_scores_ok(self):
        result = score_coldiq_compliance.invoke({
            "content_type": "linkedin_post",
            "body": "Most SaaS teams get outbound wrong.\n\nHere's the reality.\n\nThe data shows a simpler approach.\n\nWhat's your take?",
        })
        assert len(result["passing_rules"]) >= 1

    def test_linkedin_without_cta_suggests_fix(self):
        result = score_coldiq_compliance.invoke({
            "content_type": "linkedin_post",
            "body": "Just published a new blog post. Link in bio.",
        })
        assert "linkedin_cta_engagement" in result["failing_rules"]
        assert any("CTA" in s for s in result["suggestions"])

    def test_score_between_0_and_10(self):
        cases = [
            {"content_type": "cold_email", "subject": "Hi", "body": "a\n\nb\n\nc"},
            {"content_type": "cold_email", "subject": "x" * 100, "body": "spam free guaranteed"},
            {"content_type": "linkedin_post", "body": "Most people miss this.\n\nHere's why.\n\nThe approach.\n\nComments?"},
        ]
        for case in cases:
            result = score_coldiq_compliance.invoke(case)
            assert 0 <= result["score"] <= 10, f"Score {result['score']} out of range for {case}"


# ── Registry ────────────────────────────────────────────────────────────────

class TestRegistry:
    def test_contains_4_tools(self):
        assert len(COLDIQ_SKILLS) == 4

    def test_all_tools_have_names(self):
        names = {t.name for t in COLDIQ_SKILLS}
        expected = {"sales_triggers", "cold_email_sequence", "linkedin_post", "score_coldiq_compliance"}
        assert names == expected

    def test_all_tools_have_descriptions(self):
        for tool in COLDIQ_SKILLS:
            assert tool.description, f"{tool.name} has no description"


# ── Constants ───────────────────────────────────────────────────────────────

class TestConstants:
    def test_sales_triggers_has_7_categories(self):
        assert set(SALES_TRIGGERS.keys()) == {
            "hiring", "funding", "product_launch",
            "leadership_change", "regulatory", "competitive", "customer_behavior",
        }

    def test_cold_email_templates_has_3_phases(self):
        assert set(COLD_EMAIL_TEMPLATES.keys()) == {
            "pattern_interrupt", "social_proof", "direct_ask",
        }

    def test_linkedin_hook_formats_non_empty(self):
        assert len(LINKEDIN_HOOK_FORMATS) >= 5

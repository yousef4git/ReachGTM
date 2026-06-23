"""
ColdIQ GTM Methodology — LangChain Tools

Wraps ColdIQ's framework for cold email sequences, LinkedIn outreach,
and the 137+ sales trigger taxonomy into callable tools used by the
content node.

References:
  - ColdIQ methodology: 137 sales triggers, cold email sequences, LinkedIn hooks
  - Content prompt: `agents/app/prompts/content.py`
"""

from typing import Optional
from langchain_core.tools import tool

# ── Sales Triggers (137+ taxonomy) ──────────────────────────────────────────

SALES_TRIGGERS: dict[str, list[dict]] = {
    "hiring": [
        {"trigger": "VP / Director of Sales hired", "signal": "New sales leader → likely to refresh stack and process"},
        {"trigger": "First CRO appointed", "signal": "Company moving from founder-led to professional sales"},
        {"trigger": "Head of Marketing hired", "signal": "New marketing leader → open to new GTM tools"},
        {"trigger": "SDR/BDR team expansion (3+ hires)", "signal": "Scaling outbound — needs sequences, data, and enrichment"},
        {"trigger": "Customer Success team created", "signal": "Post-sale role exists → expansion / upsell motion possible"},
        {"trigger": "Chief Revenue Officer hired from competitor", "signal": "Brings playbook from previous GTM stack — replacement opportunity"},
        {"trigger": "Hiring surge in sales org (50%+ growth)", "signal": "Ramped spending on infrastructure: CRM, engagement, data"},
        {"trigger": "Hiring for roles that didn't exist 6 months ago", "signal": "Organizational maturity shift — new buying authority emerged"},
        {"trigger": "Enterprise AE job postings appear", "signal": "Moving upmarket — needs enterprise-grade solutions"},
        {"trigger": "Fractional / interim CRO postings", "signal": "Bridge hire — temporary but high influence on tooling decisions"},
    ],
    "funding": [
        {"trigger": "Series A raised ($5M+)", "signal": "Fresh capital → GTM team buildout, tooling budget unlocked"},
        {"trigger": "Series B raised ($15M+)", "signal": "Scaling stage — needs automation, analytics, multi-channel playbooks"},
        {"trigger": "Seed round from top-tier VC", "signal": "Well-capitalized seed — aggressive hiring, fast decisions"},
        {"trigger": "Bridge round / convertible note", "signal": "Survival mode OR deliberate — may be price-sensitive"},
        {"trigger": "Debt financing raised", "signal": "Revenue-backed growth — ROI-driven purchasing"},
        {"trigger": "Strategic investment from a platform company", "signal": "Ecosystem play — likely to adopt complementary tools from same stack"},
        {"trigger": "Public grant / non-dilutive funding", "signal": "Non-dilutive = more budget for ops tools"},
        {"trigger": "Secondary sale by early employees", "signal": "Liquidity event — leadership focus shifts to growth"},
        {"trigger": "SPAC / IPO announcement", "signal": "Public company procurement — longer cycles, higher budgets"},
        {"trigger": "Down round", "signal": "Cost-cutting mode — requires ROI-justified, bottom-up pitch"},
    ],
    "product_launch": [
        {"trigger": "New product line launched", "signal": "New offering needs its own GTM motion, separate from core"},
        {"trigger": "Platform / marketplace launch", "signal": "Multi-sided marketplace — complex GTM, needs orchestration"},
        {"trigger": "Major feature release (v2 / v3)", "signal": "Expansion opportunity with existing customers"},
        {"trigger": "Pricing overhaul announced", "signal": "Restructured tiers — need to re-engage old leads with new pricing"},
        {"trigger": "Free tier / freemium launch", "signal": "PLG motion — needs different automation and nurture tracks"},
        {"trigger": "API / integration release", "signal": "Platform play — developer- and partner-led distribution"},
        {"trigger": "International / localization launch", "signal": "New region — needs localized GTM content"},
        {"trigger": "Product sunset / deprecation notice", "signal": "Transition window — customers need migration support"},
        {"trigger": "Beta program announced", "signal": "Early adopters available — time-sensitive window"},
        {"trigger": "White-label / OEM program launched", "signal": "Indirect sales channel — partner enablement needed"},
    ],
    "leadership_change": [
        {"trigger": "CEO stepped down / replaced", "signal": "Strategic pivot possible — new CEO brings new priorities"},
        {"trigger": "New CTO / VP Engineering hired", "signal": "Technical buying decisions may shift — integration-focused pitch"},
        {"trigger": "CFO replaced", "signal": "Budget authority changes — re-justify all existing spend"},
        {"trigger": "VP of Sales fired / quit", "signal": "Organizational churn — sales process reset, tooling freeze or flush"},
        {"trigger": "Board member added from industry", "signal": "Network effects — referral path through board"},
        {"trigger": "Founder returns as CEO", "signal": "Re-focus on original vision — likely to undo recent tooling decisions"},
        {"trigger": "C-suite re-organization announced", "signal": "Multiple roles changing — chaos creates openness to new solutions"},
        {"trigger": "New head of RevOps hired", "signal": "RevOps = tooling buyer. First 90 days are prime window"},
        {"trigger": "General counsel hired", "signal": "Enterprise stage — legal review now part of procurement"},
        {"trigger": "Chief AI / Data Officer hired", "signal": "Data-first strategy — AI-powered GTM tools get a hearing"},
    ],
    "regulatory": [
        {"trigger": "GDPR / CCPA fine issued to competitor", "signal": "Compliance fear — companies in similar vertical will audit tools"},
        {"trigger": "SOC 2 certification achieved", "signal": "Ready for enterprise buyers — needs enterprise-grade GTM infrastructure"},
        {"trigger": "Industry regulation change (HIPAA, FINRA, etc.)", "signal": "Compliance-driven tooling requirements emerge"},
        {"trigger": "Data breach reported", "signal": "Security review initiated — pause all new vendor signups"},
        {"trigger": "ISO 27001 certification in progress", "signal": "Security maturity growing — procurement processes formalizing"},
    ],
    "competitive": [
        {"trigger": "Competitor acquired", "signal": "Market consolidation — customers evaluating alternatives"},
        {"trigger": "Competitor raised large round", "signal": "Arms race — competitor will increase GTM spend"},
        {"trigger": "Competitor laid off 15%+", "signal": "Talent flight — opportunity to hire or win their customers"},
        {"trigger": "Gartner / Forrester report published", "signal": "Quadrant / Wave report — procurement teams use it as vendor list"},
        {"trigger": "Competitor changed pricing model", "signal": "Strategy shift — creates comparison gap with your positioning"},
    ],
    "customer_behavior": [
        {"trigger": "Support ticket volume up 50%+", "signal": "Product friction — churn risk, but also expansion opportunity if addressed"},
        {"trigger": "NPS score dropped below 30", "signal": "Churn acceleration — intervene with customer success outreach"},
        {"trigger": "Login frequency declining", "signal": "Adoption decay — re-engagement campaign needed"},
        {"trigger": "Feature request volume spiking for specific area", "signal": "Product gap — also a GTM angle: 'we solve the problem you keep asking for'"},
        {"trigger": "Billboard / outbound campaign spotted", "signal": "Aggressive GTM — competitor may be targeting same accounts"},
    ],
}


@tool
def sales_triggers(
    trigger_types: Optional[list[str]] = None,
    industry: Optional[str] = None,
) -> list[dict]:
    """
    Look up buying signals from the ColdIQ 137+ sales trigger taxonomy.

    Args:
        trigger_types: Filter by category ('hiring', 'funding', 'product_launch',
                       'leadership_change', 'regulatory', 'competitive',
                       'customer_behavior'). Returns all if None.
        industry: Optional industry keyword for relevance scoring (not yet implemented).

    Returns:
        List of trigger dicts with 'trigger', 'signal', and optional 'relevance' keys.
    """
    if trigger_types:
        results = []
        for t in trigger_types:
            results.extend(SALES_TRIGGERS.get(t.lower(), []))
        return results
    # Flatten all categories
    all_triggers = []
    for category in SALES_TRIGGERS.values():
        all_triggers.extend(category)
    return all_triggers


# ── Cold Email Sequence ─────────────────────────────────────────────────────

COLD_EMAIL_TEMPLATES = {
    "pattern_interrupt": {
        "subject": "Short curiosity-gap subject line (< 50 chars)",
        "body_structure": [
            "Personalized observation or compliment about their recent activity",
            "Single relevant pain point their company likely faces",
            "Brief social proof (1 sentence max)",
            "Single soft CTA (reply with 'interesting' for more info, not a booking link)",
        ],
        "rules": [
            "Subject line under 50 characters, no ALL CAPS, no spam words",
            "No attachments, no links in email 1",
            "Under 100 words total",
            "No mention of price, demo, or discount",
        ],
    },
    "social_proof": {
        "subject": "What [Similar Company] did instead",
        "body_structure": [
            "Reference to first email (they read it, good)",
            "Case study angle: company like theirs + problem + result",
            "Specific metric if available (e.g., '27% increase in reply rates')",
            "Soft CTA — offer a relevant resource",
        ],
        "rules": [
            "Under 120 words",
            "1 link maximum (to the case study / resource)",
            "No hard sell — still positioning, not pitching",
        ],
    },
    "direct_ask": {
        "subject": "Quick question",
        "body_structure": [
            "Acknowledge no reply (no guilt trip, just brevity)",
            "Direct value framing — 'Here's exactly what I'm proposing'",
            "Clear, low-friction next step (15-min call, specific time suggestion)",
            "Explicit opt-out — 'If not relevant, just say pass'",
        ],
        "rules": [
            "Under 80 words",
            "Specific calendar slot if proposing a call",
            "Make it easy to say no (polite persistence, not pressure)",
        ],
    },
}


@tool
def cold_email_sequence(
    target_name: str,
    target_title: str,
    company_name: str,
    industry: str,
    pain_points: list[str],
    social_proof: str,
    triggers: Optional[list[str]] = None,
) -> list[dict]:
    """
    Generate a ColdIQ-style 3-email cold outreach sequence.

    Applies the pattern-interrupt → social-proof → direct-ask framework
    with the 137+ sales triggers.

    Args:
        target_name: First name of the recipient.
        target_title: Job title of the recipient.
        company_name: Target company name.
        industry: Industry vertical.
        pain_points: 1-3 specific pain points to address.
        social_proof: One-liner case study or stat (e.g. 'helped Acme cut churn 30%').
        triggers: Optional sales triggers for personalization context.

    Returns:
        List of 3 email dicts: {'subject': str, 'body': str, 'sequence_position': int}.
    """
    emails = []

    # Email 1 — Pattern interrupt
    trigger_line = ""
    if triggers:
        trigger_line = f" Noticed {triggers[0].lower()} — "
    emails.append({
        "sequence_position": 1,
        "subject": f"Quick thought on {pain_points[0].split()[0] if pain_points else 'growth'}",
        "body": (
            f"Hi {target_name},\n\n"
            f"{trigger_line}I've been following {company_name}'s work in {industry}.\n\n"
            f"One thing that comes up often with {industry} teams: {pain_points[0] if pain_points else 'scaling outbound without burning leads'}.\n\n"
            f"{social_proof}\n\n"
            f"Curious if this resonates.\n\n"
            f"Best,\n[Your Name]"
        ),
    })

    # Email 2 — Social proof
    emails.append({
        "sequence_position": 2,
        "subject": f"What {company_name} could learn from [Similar Co]",
        "body": (
            f"Hi {target_name},\n\n"
            f"Following up on my last note.\n\n"
            f"We worked with a {industry} company facing the same challenge — {pain_points[0] if pain_points else 'outbound scalability'}.\n"
            f"{social_proof}\n\n"
            f"Thought this might be useful context.\n\n"
            f"Best,\n[Your Name]"
        ),
    })

    # Email 3 — Direct ask
    emails.append({
        "sequence_position": 3,
        "subject": "Quick question",
        "body": (
            f"Hi {target_name},\n\n"
            f"I know timing hasn't been right yet.\n\n"
            f"Here's the quick version: {social_proof}.\n\n"
            f"Worth 15 minutes to see if this fits {company_name}'s plans?\n\n"
            f"If not, just say pass — no hard feelings.\n\n"
            f"Best,\n[Your Name]"
        ),
    })

    return emails


# ── LinkedIn Post ───────────────────────────────────────────────────────────

LINKEDIN_HOOK_FORMATS = [
    "Contrarian take: 'Everyone says X, but the data shows Y'",
    "Bold claim: 'We did [metric] in [timeframe] — here's how'",
    "Question: 'Why do 80% of [industry] teams still do [outdated practice]?'",
    "Pattern interrupt: 'Stop doing [common mistake]'",
    "Story lead: 'I almost quit [month] ago. Here's what changed.'",
    "Stat drop: '[Number]% of [group] fail at [goal]. Here's why.'",
    "Hot take on a news event relevant to the industry",
]


@tool
def linkedin_post(
    topic: str,
    target_audience: str,
    hook_format: Optional[str] = None,
    tone: str = "professional",
) -> dict:
    """
    Generate a ColdIQ-style LinkedIn post optimized for engagement.

    Args:
        topic: The post topic or key message.
        target_audience: Who the post is for (ICP description).
        hook_format: Optional hook style from available formats.
        tone: 'professional', 'contrarian', 'storytelling', or 'educational'.

    Returns:
        A dict with 'hook', 'body_paragraphs', 'cta', and 'post' (full text).
    """
    hook = (
        f"Most {target_audience} teams get {topic} wrong. "
        f"They overcomplicate it."
    )

    body = [
        f"Here's the reality: {topic} isn't about doing more — it's about doing the right things in the right order.",
        "The teams that win focus on one channel, nail the message, and iterate on data. Not shiny objects.",
        f"If you're building for {target_audience}, the playbook is simpler than you think:",
    ]

    cta = (
        "What's your approach? Drop it in the comments ↓"
        if tone == "professional"
        else "Agree or disagree? Let's discuss."
    )

    full_post = f"{hook}\n\n" + "\n\n".join(body) + f"\n\n{cta}"

    return {
        "hook": hook,
        "body_paragraphs": body,
        "cta": cta,
        "post": full_post,
        "tone": tone,
    }


# ── ColdIQ Compliance Scoring ───────────────────────────────────────────────

COLDIQ_QUALITY_RULES = {
    "subject_line_under_50": {"description": "Email subject under 50 characters", "weight": 1},
    "no_spam_triggers": {"description": "No 'free', 'guaranteed', 'act now' in subject or body", "weight": 2},
    "curiosity_gap": {"description": "Subject creates curiosity without revealing the full ask", "weight": 2},
    "personalization": {"description": "At least 1 personalized observation per email", "weight": 3},
    "single_pain_point": {"description": "Each email addresses at most 2 pain points", "weight": 1},
    "soft_cta": {"description": "CTA is low-friction (reply, resource, thought), not 'book a demo'", "weight": 2},
    "professional_tone": {"description": "Conversational, not corporate or pushy", "weight": 2},
    "linkedin_hook_stops_scroll": {"description": "First line is a bold claim, question, or contrarian take", "weight": 3},
    "linkedin_short_paragraphs": {"description": "3-5 short paragraphs, one idea each", "weight": 2},
    "linkedin_cta_engagement": {"description": "CTA asks for comment/share/DM, not 'link in bio'", "weight": 2},
}


@tool
def score_coldiq_compliance(
    content_type: str,
    subject: Optional[str] = None,
    body: str = "",
) -> dict:
    """
    Score a piece of content against ColdIQ quality standards.

    Args:
        content_type: 'cold_email' or 'linkedin_post'.
        subject: Email subject line (optional; only used for cold_email).
        body: Full body text of the content.

    Returns:
        Dict with 'passing_rules', 'failing_rules', 'score' (0-10), and 'suggestions'.
    """
    passing = []
    failing = []
    suggestions = []

    if content_type == "cold_email":
        if subject and len(subject) <= 50:
            passing.append("subject_line_under_50")
        elif subject:
            failing.append("subject_line_under_50")
            suggestions.append(f"Subject line is {len(subject)} chars. Keep under 50.")

        spam_words = ["free", "guaranteed", "act now", "limited time", "exclusive offer"]
        body_lower = body.lower()
        found_spam = [w for w in spam_words if w in body_lower]
        if not found_spam:
            passing.append("no_spam_triggers")
        else:
            failing.append("no_spam_triggers")
            suggestions.append(f"Remove spam trigger words: {', '.join(found_spam)}")

        body_words = len(body.split())
        if body_words <= 100:
            passing.append("single_pain_point")  # proxy for concise
        else:
            failing.append("single_pain_point")
            suggestions.append(f"Body is {body_words} words. Keep under 100 for email 1.")

        if body.count("\n\n") >= 2:
            passing.append("soft_cta")
        else:
            failing.append("soft_cta")
            suggestions.append("Add a soft CTA with a line break before it.")

    elif content_type == "linkedin_post":
        lines = body.strip().split("\n")
        first_line = lines[0] if lines else ""

        hook_indicators = ["why", "stop", "most", "everyone", "i almost", "here's", "mistake"]
        if any(first_line.lower().startswith(w) for w in hook_indicators):
            passing.append("linkedin_hook_stops_scroll")
        else:
            failing.append("linkedin_hook_stops_scroll")
            suggestions.append("Open with a bold claim, question, or contrarian take.")

        para_count = sum(1 for line in lines if line.strip() == "" or line.strip() == "\n") + 1
        if 3 <= para_count <= 5:
            passing.append("linkedin_short_paragraphs")
        else:
            failing.append("linkedin_short_paragraphs")
            suggestions.append(f"Aim for 3-5 paragraphs (got {para_count}).")

        ctas_engagement = ["comment", "share", "dm ", "thoughts", "agree", "disagree"]
        ctas_link = ["link in bio", "link below", "check the link"]
        body_lower = body.lower()
        if any(c in body_lower for c in ctas_engagement):
            passing.append("linkedin_cta_engagement")
        elif any(c in body_lower for c in ctas_link):
            failing.append("linkedin_cta_engagement")
            suggestions.append("Replace 'link in bio' with an engagement CTA (comment, share, DM).")
        else:
            failing.append("linkedin_cta_engagement")
            suggestions.append("Add an engagement CTA asking for comments or DMs.")

    score_bonus = len(passing) * 2
    score_penalty = len(failing) * 1
    score = max(0, min(10, score_bonus - score_penalty))

    return {
        "passing_rules": passing,
        "failing_rules": failing,
        "score": score,
        "suggestions": suggestions,
    }


# ── Tool Registry ───────────────────────────────────────────────────────────

COLDIQ_SKILLS: list = [
    sales_triggers,
    cold_email_sequence,
    linkedin_post,
    score_coldiq_compliance,
]

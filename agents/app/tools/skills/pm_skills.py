"""
PM-Skills — LangChain Tools (ICP & Positioning)

Deterministic, LangChain-compatible tool wrappers the strategy node calls to
build the ICP and positioning sections of a GTM strategy. No live LLM/network
calls — these are pure-Python transforms over typed inputs.

I/O contract (consumes the schema stubs from PR #8):
  - build_icp_profile   -> dict valid as shared.schemas.ICPProfile
  - score_icp_fit       -> deterministic fit score for a target account
  - positioning_statement -> Geoffrey Moore statement (-> GTMStrategy.positioning_statement)
  - value_proposition   -> dict valid as shared.schemas.ValueProp

References:
  - Schemas: `shared/schemas.py` (ICPProfile, ValueProp, GTMStrategy)
  - Sibling pattern: `agents/app/tools/skills/coldiq_skills.py`
"""

import re
from typing import Optional

from langchain_core.tools import tool

from shared.schemas import ICPProfile, ValueProp


# ── Reference data ───────────────────────────────────────────────────────────

# Buying committee composition by company-size tier. Used to complete an ICP
# when the caller doesn't supply the committee explicitly.
BUYING_COMMITTEE_BY_TIER: dict[str, list[str]] = {
    "smb": ["Founder / CEO", "Head of Sales"],
    "mid_market": ["VP Sales", "VP Marketing", "RevOps Lead", "CFO"],
    "enterprise": [
        "CRO",
        "VP Marketing",
        "RevOps Director",
        "CFO",
        "Procurement",
        "Legal / Security",
    ],
}

# Sensible default disqualifiers when the caller doesn't provide any.
DEFAULT_DISQUALIFIERS: list[str] = [
    "No dedicated GTM / sales function",
    "Budget below the stated range",
    "No executive sponsor identified",
]

# Weighting for the ICP fit score — must sum to 100.
FIT_WEIGHTS: dict[str, int] = {
    "industry": 40,
    "size": 30,
    "budget": 15,
    "signals": 15,
}


def _indefinite_article(noun_phrase: str) -> str:
    """Pick "a" / "an" from the first letter of a noun phrase.

    A first-letter heuristic — correct for the common cases (e.g. "an AI
    platform", "a CRM"), not for vowel-sound exceptions like "an hour" or
    "a university".
    """
    return "an" if noun_phrase[:1].lower() in "aeiou" else "a"


def _company_size_tier(company_size: str) -> str:
    """Map a free-text company-size string to a tier.

    Uses the largest number found (the range ceiling) so "50-200 employees"
    is treated as mid-market rather than SMB. Falls back to mid-market when
    no number is present.
    """
    nums = re.findall(r"\d+", company_size.replace(",", ""))
    if not nums:
        return "mid_market"
    ceiling = max(int(n) for n in nums)
    if ceiling < 100:
        return "smb"
    if ceiling <= 1000:
        return "mid_market"
    return "enterprise"


# ── ICP ──────────────────────────────────────────────────────────────────────

@tool
def build_icp_profile(
    title: str,
    industry: str,
    company_size: str,
    budget_range: str,
    pain_points: list[str],
    goals: list[str],
    buying_committee: Optional[list[str]] = None,
    disqualifiers: Optional[list[str]] = None,
) -> dict:
    """
    Assemble a complete, schema-valid Ideal Customer Profile (ICP).

    Fills in a sensible buying committee (derived from company size) and a
    default set of disqualifiers when the caller omits them, so the strategy
    node always receives a fully-populated ICPProfile.

    Args:
        title: Target persona's job title (e.g. "VP of Sales").
        industry: Industry vertical (e.g. "B2B SaaS").
        company_size: Free-text size, e.g. "50-200 employees" or "1000+".
        budget_range: Expected budget band, e.g. "$10k-$50k / yr".
        pain_points: Specific pains this ICP feels.
        goals: Outcomes this ICP is trying to achieve.
        buying_committee: Roles involved in the purchase. Derived from
            company size when not provided.
        disqualifiers: Signals that rule an account out. Defaults applied
            when not provided.

    Returns:
        A dict that validates against shared.schemas.ICPProfile.
    """
    committee = buying_committee or BUYING_COMMITTEE_BY_TIER[_company_size_tier(company_size)]
    disqs = disqualifiers or list(DEFAULT_DISQUALIFIERS)

    profile = ICPProfile(
        title=title,
        industry=industry,
        company_size=company_size,
        budget_range=budget_range,
        pain_points=pain_points,
        goals=goals,
        buying_committee=committee,
        disqualifiers=disqs,
    )
    return profile.model_dump()


@tool
def score_icp_fit(
    icp: dict,
    account_industry: str,
    account_size: str,
    account_budget: Optional[str] = None,
    account_signals: Optional[list[str]] = None,
) -> dict:
    """
    Score how well a target account matches an ICP (0-100, deterministic).

    Lets the strategy node rank or qualify accounts against the ICP without an
    LLM call. Scoring is weighted: industry (40), size tier (30),
    budget present (15), buying signals present (15).

    MVP limitations (intentional, not yet expanded):
        - Industry matching uses a simple case-insensitive equality / substring
          heuristic; it does not do semantic or taxonomy-aware matching.
        - Budget scoring is presence-based only — it awards points when a budget
          is supplied and does not parse or compare against the ICP budget range.

    Args:
        icp: An ICPProfile-shaped dict (e.g. the output of build_icp_profile).
        account_industry: The target account's industry.
        account_size: The target account's free-text size.
        account_budget: The account's known budget, if any.
        account_signals: Observed buying signals, if any.

    Returns:
        Dict with 'score' (int 0-100), 'tier' ('A' | 'B' | 'C'),
        'matched' (list[str]) and 'gaps' (list[str]).
    """
    profile = ICPProfile(**icp)  # validate the incoming ICP shape
    matched: list[str] = []
    gaps: list[str] = []
    score = 0

    icp_industry = profile.industry.strip().lower()
    acct_industry = account_industry.strip().lower()
    if icp_industry == acct_industry:
        score += FIT_WEIGHTS["industry"]
        matched.append(f"Industry matches ICP ({profile.industry})")
    elif icp_industry in acct_industry or acct_industry in icp_industry:
        score += FIT_WEIGHTS["industry"] // 2
        matched.append(f"Industry partially matches ICP ({profile.industry})")
    else:
        gaps.append(f"Industry '{account_industry}' differs from ICP '{profile.industry}'")

    if _company_size_tier(profile.company_size) == _company_size_tier(account_size):
        score += FIT_WEIGHTS["size"]
        matched.append("Company size in ICP tier")
    else:
        gaps.append("Company size outside ICP tier")

    if account_budget:
        score += FIT_WEIGHTS["budget"]
        matched.append("Budget known")
    else:
        gaps.append("No budget information")

    if account_signals:
        score += FIT_WEIGHTS["signals"]
        matched.append(f"{len(account_signals)} buying signal(s) present")
    else:
        gaps.append("No buying signals observed")

    tier = "A" if score >= 75 else "B" if score >= 50 else "C"
    return {"score": score, "tier": tier, "matched": matched, "gaps": gaps}


# ── Positioning ──────────────────────────────────────────────────────────────

@tool
def positioning_statement(
    product_name: str,
    target_customer: str,
    need: str,
    market_category: str,
    key_benefit: str,
    primary_competitor: str,
    primary_differentiation: str,
) -> dict:
    """
    Build a Geoffrey Moore positioning statement (deterministic).

    Produces the canonical "For [target] who [need], [product] is a [category]
    that [benefit]. Unlike [competitor], [product] [differentiation]." form.
    The 'statement' field is ready to drop into GTMStrategy.positioning_statement.

    Args:
        product_name: Name of the product / company.
        target_customer: Who it's for (ideally the ICP title + segment).
        need: The need or opportunity, phrased to follow "who ...".
        market_category: The market the product competes in.
        key_benefit: The compelling reason to buy, phrased to follow "that ...".
        primary_competitor: The main alternative.
        primary_differentiation: What we do differently, phrased to follow
            "[product] ...".

    Returns:
        Dict with 'statement' (str) and 'components' (the structured inputs).
    """
    statement = (
        f"For {target_customer} who {need}, "
        f"{product_name} is {_indefinite_article(market_category)} {market_category} that {key_benefit}. "
        f"Unlike {primary_competitor}, {product_name} {primary_differentiation}."
    )
    return {
        "statement": statement,
        "components": {
            "product_name": product_name,
            "target_customer": target_customer,
            "need": need,
            "market_category": market_category,
            "key_benefit": key_benefit,
            "primary_competitor": primary_competitor,
            "primary_differentiation": primary_differentiation,
        },
    }


@tool
def value_proposition(
    headline: str,
    target_customer: str,
    key_benefit: str,
    proof_points: list[str],
    differentiators: list[str],
    subheadline: Optional[str] = None,
) -> dict:
    """
    Assemble a schema-valid value proposition (ValueProp).

    Generates a subheadline from the target and benefit when one isn't supplied.

    Args:
        headline: The primary value claim.
        target_customer: Who the value prop speaks to.
        key_benefit: The core outcome delivered.
        proof_points: Evidence backing the claim (metrics, customers, awards).
        differentiators: What sets the product apart from alternatives.
        subheadline: Optional supporting line; derived when omitted.

    Returns:
        A dict that validates against shared.schemas.ValueProp.
    """
    sub = subheadline or f"Built for {target_customer} — {key_benefit}."
    prop = ValueProp(
        headline=headline,
        subheadline=sub,
        proof_points=proof_points,
        differentiators=differentiators,
    )
    return prop.model_dump()


# ── Tool Registry ────────────────────────────────────────────────────────────

PM_SKILLS: list = [
    build_icp_profile,
    score_icp_fit,
    positioning_statement,
    value_proposition,
]

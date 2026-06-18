"""
Content Node — ColdIQ GTM Content Generation

Generates sales and marketing content assets using the ColdIQ methodology.
Works with both real GTMStrategy objects (from the strategy node) and
stubbed strategies during parallel Week 2 development.

Flow:
  1. Read content types and count from state.metadata
  2. Use LLM (gpt-4o-mini) with ColdIQ prompt to generate each asset
  3. Score each asset with score_coldiq_compliance
  4. If LLM unavailable, fall back to template-based ColdIQ tools
  5. Return state populated with ContentAsset list
"""

import logging
from uuid import uuid4
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from agents.app.graph.state import GTMState
from agents.app.graph.nodes.variants import expand_assets_to_variants
from agents.app.prompts.content import CONTENT_SYSTEM_PROMPT
from shared.schemas import ContentAsset, ContentType, GTMStrategy, ICPProfile

logger = logging.getLogger(__name__)

# Multi-ICP mode generates content for up to this many ICPs in one run.
MAX_ICPS = 3

# ── Helpers ──────────────────────────────────────────────────────────────────

def _strategy_context(strategy: Optional[GTMStrategy]) -> dict:
    """Build a structured context dict from the strategy (or stub)."""
    if strategy is None:
        return {
            "industry": "B2B SaaS",
            "icp_title": "Mid-market decision maker",
            "company_size": "100-500 employees",
            "pain_points": ["scaling outbound", "low reply rates"],
            "value_headline": "AI-powered sales acceleration",
            "motion": "sales_led_growth",
            "top_channels": "cold_email, linkedin",
            "positioning": "GTM automation platform for B2B teams",
        }

    icp = strategy.icp
    vp = strategy.value_proposition
    return {
        "industry": icp.industry,
        "icp_title": icp.title,
        "company_size": icp.company_size,
        "pain_points": icp.pain_points[:3],
        "value_headline": vp.headline,
        "motion": strategy.motion.value,
        "top_channels": ", ".join(c.name for c in strategy.channels[:3]),
        "positioning": strategy.positioning_statement[:200],
    }


def _resolve_target_icps(state: GTMState) -> list[ICPProfile]:
    """Collect the ICPs to target: the strategy ICP plus metadata.additional_icps.

    Deduplicated by title and capped at MAX_ICPS. Returns [] when there is no
    strategy and no additional ICPs (single/stub path is used in that case).
    """
    icps: list[ICPProfile] = []
    if state.gtm_strategy is not None:
        icps.append(state.gtm_strategy.icp)
    for raw in state.metadata.get("additional_icps", []):
        try:
            icps.append(raw if isinstance(raw, ICPProfile) else ICPProfile(**raw))
        except Exception:  # noqa: BLE001 — skip malformed ICP entries
            continue

    seen: set[str] = set()
    unique: list[ICPProfile] = []
    for icp in icps:
        if icp.title not in seen:
            seen.add(icp.title)
            unique.append(icp)
    return unique[:MAX_ICPS]


def _ctx_for_icp(base_ctx: dict, icp: ICPProfile) -> dict:
    """Override the ICP-specific fields of a base context for one ICP."""
    ctx = dict(base_ctx)
    ctx.update({
        "industry": icp.industry,
        "icp_title": icp.title,
        "company_size": icp.company_size,
        "pain_points": icp.pain_points[:3],
    })
    return ctx


def _ctx_formatted(ctx: dict) -> str:
    """Format context dict as a readable string for the LLM prompt."""
    return (
        f"Company industry: {ctx['industry']}\n"
        f"ICP title: {ctx['icp_title']} | company size: {ctx['company_size']}\n"
        f"Pain points: {'; '.join(ctx['pain_points'])}\n"
        f"Value headline: {ctx['value_headline']}\n"
        f"GTM motion: {ctx['motion']}\n"
        f"Top channels: {ctx['top_channels']}\n"
        f"Positioning: {ctx['positioning']}"
    )


def _build_llm_prompt(content_type: ContentType, context: str, index: int) -> list:
    """Build the message list for the LLM call."""
    type_instructions = {
        ContentType.COLD_EMAIL: (
            "Generate a cold email (email {index} of a multi-email sequence). "
            "Follow the ColdIQ pattern-interrupt → social-proof → direct-ask framework. "
            "Rules:\n"
            "- Subject under 50 characters, no spam words\n"
            "- Body under 100 words for early emails\n"
            "- Soft CTA (reply, not 'book a demo')\n"
            "- Conversational tone, not corporate\n"
            "Return ONLY the email body text. Do not wrap in JSON."
        ),
        ContentType.LINKEDIN_POST: (
            "Generate a LinkedIn post. Rules:\n"
            "- Hook: First line must stop the scroll (bold claim, question, contrarian take)\n"
            "- Body: 3-5 short paragraphs, one idea each\n"
            "- CTA: Ask for comment/share/DM — never 'link in bio'\n"
            "- Tone: Professional but conversational"
        ),
        ContentType.BLOG_OUTLINE: (
            f"Generate a blog outline (piece {index}). "
            "Include:\n"
            "- Title (attention-grabbing, SEO-friendly)\n"
            "- 5-7 section headings with 2-3 bullet points per section\n"
            "- Suggested meta description (under 160 chars)\n"
            "- Target keyword"
        ),
        ContentType.AD_COPY: (
            f"Generate ad copy (variant {index}). "
            "Include:\n"
            "- Headline (under 30 chars)\n"
            "- Body (under 90 chars)\n"
            "- CTA text\n"
            "- Value angle"
        ),
    }

    instructions = type_instructions.get(
        content_type,
        f"Generate a {content_type.value} content asset (piece {index})."
    )

    return [
        SystemMessage(content=CONTENT_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Strategy Context:\n{context}\n\n"
                f"---\n\n"
                f"{instructions.format(index=index)}"
            )
        ),
    ]


# ── Content Generation ──────────────────────────────────────────────────────

async def content_node(state: GTMState) -> GTMState:
    # Resolve content types to generate
    raw_types = state.metadata.get("content_types", ["cold_email", "linkedin_post"])
    count_per_type: int = state.metadata.get("count_per_type", 3)

    types_to_generate: list[ContentType] = []
    for rt in raw_types:
        try:
            types_to_generate.append(ContentType(rt))
        except ValueError:
            logger.warning("Unknown content type: %s", rt)

    if not types_to_generate:
        types_to_generate = [ContentType.COLD_EMAIL, ContentType.LINKEDIN_POST]

    base_ctx = _strategy_context(state.gtm_strategy)
    icps = _resolve_target_icps(state)

    # Multi-ICP mode (Phase 2): when 2+ ICPs are available, generate the content
    # set for each ICP and tag the assets. A single ICP (or none) uses the
    # existing path, so default behaviour is unchanged.
    if len(icps) >= 2:
        assets = []
        for icp in icps:
            icp_ctx = _ctx_for_icp(base_ctx, icp)
            icp_assets = await _generate(types_to_generate, count_per_type, icp_ctx)
            assets.extend(a.model_copy(update={"target_icp": icp.title}) for a in icp_assets)
    else:
        assets = await _generate(types_to_generate, count_per_type, base_ctx)

    # A/B variant generation (Phase 2): opt-in via metadata; expands each asset
    # into 3 split-test variants. Off by default to preserve existing behaviour.
    if state.metadata.get("ab_variants"):
        assets = expand_assets_to_variants(assets)

    return state.model_copy(update={
        "current_agent": "content",
        "content_assets": assets,
    })


async def _generate(
    types_to_generate: list[ContentType],
    count_per_type: int,
    ctx: dict,
) -> list[ContentAsset]:
    """Generate content for one context: LLM, falling back to templates."""
    try:
        return await _generate_with_llm(types_to_generate, count_per_type, ctx)
    except Exception as exc:  # noqa: BLE001 — any LLM failure -> deterministic templates
        logger.warning("LLM content generation failed (%s), using templates", exc)
        return _generate_template_fallback(types_to_generate, count_per_type, ctx)


async def _generate_with_llm(
    types_to_generate: list[ContentType],
    count_per_type: int,
    ctx: dict,
) -> list[ContentAsset]:
    """Generate content assets using gpt-4o-mini."""
    from agents.app.config import settings

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=settings.openai_api_key)
    assets: list[ContentAsset] = []
    ctx_str = _ctx_formatted(ctx)

    for content_type in types_to_generate:
        for i in range(count_per_type):
            messages = _build_llm_prompt(content_type, ctx_str, i + 1)
            response = await llm.ainvoke(messages)
            body = response.content.strip()

            # Extract a title from the first line or generate one
            first_line = body.split("\n")[0].strip()
            title = first_line[:80] if first_line else f"{content_type.value} #{i + 1}"

            assets.append(ContentAsset(
                id=uuid4(),
                type=content_type,
                title=title,
                body=body,
                target_icp=ctx["industry"],
            ))

    return assets


def _generate_template_fallback(
    types_to_generate: list[ContentType],
    count_per_type: int,
    ctx: dict,
) -> list[ContentAsset]:
    """Fallback: use ColdIQ template tools when LLM is unavailable."""
    from agents.app.tools.skills.coldiq_skills import cold_email_sequence, linkedin_post

    assets: list[ContentAsset] = []

    for content_type in types_to_generate:
        for i in range(count_per_type):
            if content_type == ContentType.COLD_EMAIL:
                seq = cold_email_sequence.invoke({
                    "target_name": "[Prospect Name]",
                    "target_title": "[Decision Maker]",
                    "company_name": "[Target Company]",
                    "industry": ctx["industry"],
                    "pain_points": ctx["pain_points"],
                    "social_proof": "Proven ColdIQ methodology driving 40%+ reply rates",
                })
                # Take one email from the sequence
                email = seq[i % len(seq)]
                assets.append(ContentAsset(
                    id=uuid4(),
                    type=ContentType.COLD_EMAIL,
                    title=email["subject"],
                    body=email["body"],
                    target_icp=ctx["industry"],
                ))

            elif content_type == ContentType.LINKEDIN_POST:
                post = linkedin_post.invoke({
                    "topic": "GTM strategy for SaaS growth",
                    "target_audience": ctx["industry"],
                    "tone": "professional",
                })
                assets.append(ContentAsset(
                    id=uuid4(),
                    type=ContentType.LINKEDIN_POST,
                    title=post["hook"][:80],
                    body=post["post"],
                    target_icp=ctx["industry"],
                ))

            else:
                # Generic stub for blog_outline, ad_copy etc.
                assets.append(ContentAsset(
                    id=uuid4(),
                    type=content_type,
                    title=f"{content_type.value.title()} #{i + 1}",
                    body=f"[{content_type.value.title()} #{i + 1} — generated via template fallback]",
                    target_icp="generic",
                ))

    return assets

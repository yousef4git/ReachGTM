from __future__ import annotations

from shared.schemas import (
    CompanyProfile,
    Competitor,
    ICPProfile,
    MarketSize,
    ResearchReport,
    Segment,
    Signal,
)
from agents.app.graph.state import GTMState


def _get_user_goal(state: GTMState) -> str:
    """Extract the latest user goal from the state messages or metadata."""
    if state.messages:
        last_message = state.messages[-1]
        if isinstance(last_message, dict):
            return str(last_message.get("content", "Create a GTM research report"))
        return str(last_message)

    return str(state.metadata.get("goal", "Create a GTM research report"))


async def _run_perplexity_search(query: str) -> list[str]:
    """Call the Perplexity MCP tool if available and return source-like text."""
    try:
        from agents.app.tools.mcp_client import get_mcp_tools
        tools = await get_mcp_tools()
        if not tools:
            return []

        tool = tools[0]
        result = await tool.ainvoke({"query": query})

        if isinstance(result, str):
            return [result]

        return [str(result)]
    except Exception as exc:
        return [f"perplexity_error:{type(exc).__name__}"]


async def _invoke_mcp_tool(server: str, name_contains: str, args: dict) -> list[str]:
    """Best-effort: invoke an MCP tool from `server` whose name matches.

    Returns the tool output as a one-item list of text, or [] when the server is
    unavailable. Never raises — failures degrade to an error-tagged source.
    """
    try:
        from agents.app.tools.mcp_client import get_mcp_tools
        tools = await get_mcp_tools(server)
        if not tools:
            return []
        tool = next((t for t in tools if name_contains in t.name.lower()), tools[0])
        result = await tool.ainvoke(args)
        return [result if isinstance(result, str) else str(result)]
    except Exception as exc:
        return [f"{server}_error:{type(exc).__name__}"]


async def _run_databar_enrich(company_name: str) -> list[str]:
    """Enrich a company via the Databar MCP tool (no-op when unconfigured)."""
    return await _invoke_mcp_tool("databar", "enrich", {"company": company_name})


async def _run_fetch_url(url: str) -> list[str]:
    """Fetch a URL's content via the Fetch MCP tool (no-op when unconfigured)."""
    return await _invoke_mcp_tool("fetch", "fetch", {"url": url})


def _build_fallback_report(state: GTMState, goal: str, sources: list[str]) -> ResearchReport:
    """Build a schema-valid ResearchReport even when live MCP search is unavailable."""
    company_profile = CompanyProfile(
        name=str(state.metadata.get("company_name", "Example Company")),
        website=state.metadata.get("website"),
        industry=str(state.metadata.get("industry", "B2B SaaS")),
        stage=str(state.metadata.get("stage", "seed")),
        description=str(
            state.metadata.get(
                "description",
                f"Company context inferred from user goal: {goal}",
            )
        ),
    )

    return ResearchReport(
        company_profile=company_profile,
        market_size=MarketSize(
            tam="Unknown",
            sam="Unknown",
            som="Unknown",
            source="Perplexity MCP fallback; replace with live source when available",
            year=2026,
        ),
        competitors=[
            Competitor(
                name="Competitor research pending",
                website=None,
                positioning="Needs live market research from Perplexity MCP.",
                strengths=["Established market presence"],
                weaknesses=["Not enough verified data yet"],
                pricing_model=None,
            )
        ],
        segments=[
            Segment(
                name="Initial target segment",
                description="A preliminary segment inferred from the user's GTM goal.",
                size_estimate="Unknown",
                pain_points=["Needs faster GTM research", "Needs clearer positioning"],
                buying_triggers=["New product launch", "Need for growth automation"],
            )
        ],
        icp=ICPProfile(
            title="Growth or Marketing Lead",
            industry=company_profile.industry,
            company_size="10-200 employees",
            budget_range="Unknown",
            pain_points=["Manual market research", "Slow content production"],
            goals=["Launch campaigns faster", "Improve positioning consistency"],
            buying_committee=["Founder", "Marketing Manager", "Growth Lead"],
            disqualifiers=["No active GTM motion", "No clear product offering"],
        ),
        signals=[
            Signal(
                type="market_research",
                description="User requested GTM research and strategy support.",
                relevance="Indicates need for structured market and competitor analysis.",
            )
        ],
        sources=sources or ["fallback:no-live-search"],
    )


async def research_node(state: GTMState) -> GTMState:
    """Research node: uses Perplexity MCP and writes a ResearchReport into state."""
    goal = _get_user_goal(state)
    query = f"Market research, competitors, ICP, and GTM trends for: {goal}"

    sources: list[str] = []

    try:
        sources = await _run_perplexity_search(query)
    except Exception as exc:
        sources = [f"perplexity_error:{type(exc).__name__}"]

    # Best-effort enrichment via Databar + Fetch MCP. Both no-op (return []) when
    # not configured, so this never breaks the offline / stub path.
    company_name = state.metadata.get("company_name")
    if company_name:
        sources += await _run_databar_enrich(str(company_name))

    website = state.metadata.get("website")
    if website:
        sources += await _run_fetch_url(str(website))

    report = _build_fallback_report(state, goal, sources)

    return state.model_copy(
        update={
            "current_agent": "research",
            "research_report": report,
        }
    )
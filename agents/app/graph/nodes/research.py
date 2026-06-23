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


_RESEARCH_SYSTEM_PROMPT = (
    "You are a senior B2B go-to-market research analyst. Given a user's GTM goal "
    "and any known company context, produce a rigorous, realistic market research "
    "report: company profile, market sizing (TAM/SAM/SOM with reasoning), 3-5 real "
    "named competitors with positioning/strengths/weaknesses, 2-3 customer segments, "
    "a concrete ICP, and notable market signals. Be specific and concrete — use real "
    "company and category names where you can. Never invent precise statistics you "
    "cannot justify; when a number is an estimate, say so in the relevant field."
)


async def _kb_context(state: GTMState, goal: str) -> str:
    """Retrieve the company's own uploaded knowledge (sales decks, product docs,
    competitive intel) and format it for the research prompt. No-op (returns "")
    when no retriever is registered or the KB is empty, so the offline/stub path
    is unaffected. This grounds the whole downstream pipeline in company docs.
    """
    try:
        from agents.app.tools.retriever_registry import get_retriever

        retriever = get_retriever()
        if retriever is None:
            return ""
        chunks = await retriever.retrieve(
            query=goal, namespace=str(state.company_id), top_k=6
        )
        if not chunks:
            return ""
        joined = "\n\n".join(f"- {c['content'][:600]}" for c in chunks)
        return (
            "\n\nCompany knowledge base (the company's OWN uploaded docs — treat as "
            "authoritative for product, ICP, positioning, and competitors; prefer these "
            "over generic web results when they conflict):\n" + joined
        )
    except Exception:  # noqa: BLE001 — KB grounding is best-effort, never breaks research
        return ""


async def _generate_report_llm(state: GTMState, goal: str) -> ResearchReport | None:
    """Generate a real, structured ResearchReport with gpt-4o-mini.

    Returns None when no OpenAI key is configured or the call fails, so the caller
    can fall back to the deterministic stub. Uses LangChain structured output so the
    model is constrained to the ResearchReport schema.
    """
    from agents.app.config import settings

    if not settings.openai_api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.4,
            api_key=settings.openai_api_key,
        ).with_structured_output(ResearchReport)

        context_bits = []
        for field in ("company_name", "website", "industry", "stage", "description"):
            value = state.metadata.get(field)
            if value:
                context_bits.append(f"{field}: {value}")
        context = "\n".join(context_bits) or "(no extra company context provided)"

        # Ground the agent in live web results (no-op when SERPER_API_KEY unset).
        from agents.app.tools.serper_search import web_search, format_results

        search_results = await web_search(
            f"market research, competitors, ICP, and GTM trends for: {goal}"
        )
        if search_results:
            web_block = (
                "\n\nLive web search results (use these to ground your report; "
                "cite the relevant links in `sources`):\n"
                f"{format_results(search_results)}"
            )
        else:
            web_block = ""

        # Ground in the company's own uploaded knowledge base (no-op when empty).
        kb_block = await _kb_context(state, goal)

        human = (
            f"GTM goal:\n{goal}\n\nKnown company context:\n{context}"
            f"{kb_block}{web_block}\n\nProduce the research report now."
        )

        report = await llm.ainvoke(
            [
                {"role": "system", "content": _RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": human},
            ]
        )
        return report
    except Exception:
        return None


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
            source="Heuristic fallback (no OpenAI key set); replace with live data",
            year=2026,
        ),
        competitors=[
            Competitor(
                name="Competitor research pending",
                website=None,
                positioning="Needs live market research (set OPENAI_API_KEY).",
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
    """Research node: generate a ResearchReport with an OpenAI agent.

    Primary path is an LLM (gpt-4o-mini) constrained to the ResearchReport schema.
    When no OpenAI key is set (or the call fails) it degrades to a deterministic
    stub so the pipeline never breaks. Databar/Fetch MCP enrichment is best-effort
    and no-ops when unconfigured.
    """
    goal = _get_user_goal(state)

    sources: list[str] = []

    # Best-effort enrichment via Databar + Fetch MCP. Both no-op (return []) when
    # not configured, so this never breaks the offline / stub path.
    company_name = state.metadata.get("company_name")
    if company_name:
        sources += await _run_databar_enrich(str(company_name))

    website = state.metadata.get("website")
    if website:
        sources += await _run_fetch_url(str(website))

    report = await _generate_report_llm(state, goal)
    if report is None:
        report = _build_fallback_report(state, goal, sources)
    elif sources:
        # Preserve any live enrichment sources alongside the LLM-generated report.
        report = report.model_copy(update={"sources": list(report.sources) + sources})

    return state.model_copy(
        update={
            "current_agent": "research",
            "research_report": report,
        }
    )
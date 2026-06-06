from agents.app.graph.state import GTMState

async def research_node(state: GTMState) -> GTMState:
    # TODO Epic 2 PR #10 — Perplexity MCP market research
    return state.model_copy(update={"current_agent": "research"})

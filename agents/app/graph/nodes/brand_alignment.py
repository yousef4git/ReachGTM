from agents.app.graph.state import GTMState

async def brand_alignment_node(state: GTMState) -> GTMState:
    # TODO Epic 2 PR #13 — RAG-based brand validation
    return state.model_copy(update={"current_agent": "brand_alignment"})

from agents.app.graph.state import GTMState

async def content_node(state: GTMState) -> GTMState:
    # TODO Epic 2 PR #12 — ColdIQ content generation
    return state.model_copy(update={"current_agent": "content"})

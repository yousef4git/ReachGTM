from agents.app.graph.state import GTMState

async def strategy_node(state: GTMState) -> GTMState:
    # TODO Epic 2 PR #11 — GTM strategy generation
    return state.model_copy(update={"current_agent": "strategy"})

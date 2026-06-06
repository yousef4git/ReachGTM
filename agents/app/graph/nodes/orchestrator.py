from agents.app.graph.state import GTMState

async def orchestrator_node(state: GTMState) -> GTMState:
    # TODO Epic 2: Parse user intent and route to appropriate sub-agent
    return state.model_copy(update={"current_agent": "orchestrator"})

from __future__ import annotations

from agents.app.graph.state import GTMState

# Canonical entry node for the GTM graph. Parses the user's goal from the
# incoming state and decides which stage of the pipeline to enter, based on
# what has already been produced. This is the node pattern other nodes copy:
# pure async function, deterministic, returns an updated copy of the state.


def _extract_goal(state: GTMState) -> str:
    """Pull the latest user goal from messages, falling back to metadata."""
    if state.messages:
        last = state.messages[-1]
        if isinstance(last, dict):
            return str(last.get("content", "")).strip() or _goal_from_metadata(state)
        return str(last).strip() or _goal_from_metadata(state)
    return _goal_from_metadata(state)


def _goal_from_metadata(state: GTMState) -> str:
    return str(state.metadata.get("goal", "Create a GTM strategy"))


def decide_route(state: GTMState) -> str:
    """Decide the next pipeline stage from what the state already contains.

    - strategy already produced  -> generate content
    - research done, no strategy -> generate strategy
    - nothing yet                -> start with research
    """
    if state.gtm_strategy is not None:
        return "content"
    if state.research_report is not None:
        return "strategy"
    return "research"


async def orchestrator_node(state: GTMState) -> GTMState:
    """Parse intent, decide the route, and record both on the state."""
    goal = _extract_goal(state)
    route = decide_route(state)

    metadata = {**state.metadata, "goal": goal, "route": route}

    return state.model_copy(
        update={
            "current_agent": "orchestrator",
            "metadata": metadata,
        }
    )

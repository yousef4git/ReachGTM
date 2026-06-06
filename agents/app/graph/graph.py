from langgraph.graph import StateGraph, START, END
from agents.app.graph.state import GTMState
from agents.app.graph.nodes.orchestrator import orchestrator_node
from agents.app.graph.nodes.research import research_node
from agents.app.graph.nodes.strategy import strategy_node
from agents.app.graph.nodes.content import content_node
from agents.app.graph.nodes.brand_alignment import brand_alignment_node

def _route_from_orchestrator(state: GTMState) -> str:
    if state.gtm_strategy is not None:
        return "content"
    return "research"

builder = StateGraph(GTMState)

builder.add_node("orchestrator", orchestrator_node)
builder.add_node("research", research_node)
builder.add_node("strategy", strategy_node)
builder.add_node("content", content_node)
builder.add_node("brand_alignment", brand_alignment_node)

builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", _route_from_orchestrator, {
    "research": "research",
    "content": "content",
})
builder.add_edge("research", "strategy")
builder.add_edge("strategy", "content")
builder.add_edge("content", "brand_alignment")
builder.add_edge("brand_alignment", END)

graph = builder.compile()

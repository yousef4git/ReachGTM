import pytest
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState
import uuid

def test_graph_compiles():
    """Verify the StateGraph compiles without error."""
    assert graph is not None

@pytest.mark.asyncio
async def test_graph_runs_stub_nodes():
    """Verify all stub nodes return state with current_agent set."""
    state = GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    result = await graph.ainvoke(state.model_dump())
    assert result["current_agent"] == "brand_alignment"

"""Tests for the agents-side graph event stream (PR #14).

Runs the real graph with external boundaries (Perplexity MCP, OpenAI) forced
into their offline fallbacks, so the event stream is deterministic and
network-free.
"""
import pytest

import agents.app.tools.mcp_client as mcp_client
from agents.app.config import settings
from agents.app.graph.stream import build_initial_state, stream_graph_events, format_sse
from shared.schemas import AgentEvent, AgentEventType


@pytest.fixture
def offline(monkeypatch):
    async def _no_tools(*args, **kwargs):
        return []

    monkeypatch.setattr(mcp_client, "get_mcp_tools", _no_tools)
    monkeypatch.setattr(settings, "openai_api_key", "")


async def _collect(state) -> list[AgentEvent]:
    return [ev async for ev in stream_graph_events(state)]


@pytest.mark.asyncio
async def test_stream_starts_with_start_and_ends_with_done(offline):
    state = build_initial_state(
        company_id=None, user_id=None,
        goal="Launch our B2B SaaS analytics product",
        content_types=["cold_email"], count_per_type=1,
    )
    events = await _collect(state)

    assert events[0].event == AgentEventType.AGENT_START
    assert events[-1].event == AgentEventType.DONE
    types = [e.event for e in events]
    # ordered: start ... complete ... done, with no error on the happy path
    assert AgentEventType.AGENT_COMPLETE in types
    assert types.index(AgentEventType.AGENT_COMPLETE) < types.index(AgentEventType.DONE)
    assert AgentEventType.ERROR not in types


@pytest.mark.asyncio
async def test_stream_reports_progress_and_outputs(offline):
    state = build_initial_state(
        company_id=None, user_id=None,
        goal="Launch product", content_types=["cold_email"], count_per_type=2,
    )
    events = await _collect(state)
    types = [e.event for e in events]

    assert AgentEventType.AGENT_PROGRESS in types
    assert AgentEventType.AGENT_OUTPUT in types
    # the brand_alignment node is the last graph node to report progress
    progress_agents = [e.agent for e in events if e.event == AgentEventType.AGENT_PROGRESS]
    assert "brand_alignment" in progress_agents

    # completion summary reflects produced artifacts
    complete = next(e for e in events if e.event == AgentEventType.AGENT_COMPLETE)
    assert complete.data["content_assets"] >= 1


def test_format_sse_frame_shape():
    frame = format_sse(AgentEvent(event=AgentEventType.AGENT_START, message="hi"))
    assert frame.startswith("event: agent_start\n")
    assert "data: " in frame
    assert frame.endswith("\n\n")

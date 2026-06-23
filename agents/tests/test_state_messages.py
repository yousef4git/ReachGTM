"""Tests for the GTMState messages reducer (bug: add_messages vs dict coercion).

Covers the reducer in isolation and the end-to-end regression: a graph run
carrying real chat messages must not raise (it used to fail mid-pipeline when
add_messages turned dicts into Message objects).
"""
import uuid

import pytest
from langchain_core.messages import HumanMessage

import agents.app.tools.mcp_client as mcp_client
from agents.app.config import settings
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState, merge_messages
from shared.schemas import GTMState as BaseGTMState


# ── reducer in isolation ─────────────────────────────────────────────────────

class TestMergeMessages:
    def test_dict_is_kept_as_dict_with_id(self):
        out = merge_messages([], [{"role": "user", "content": "hi"}])
        assert len(out) == 1
        assert out[0]["role"] == "user" and out[0]["content"] == "hi"
        assert "id" in out[0]  # id assigned for dedupe

    def test_langchain_message_is_normalised_to_dict(self):
        out = merge_messages([], [HumanMessage(content="hello")])
        assert out[0] == {"role": "user", "content": "hello", "id": out[0]["id"]}
        assert isinstance(out[0], dict)

    def test_single_item_right_is_accepted(self):
        out = merge_messages([], {"role": "user", "content": "x"})
        assert len(out) == 1

    def test_dedupes_by_id_on_re_emit(self):
        first = merge_messages([], [{"role": "user", "content": "hi"}])
        # re-emitting the same (id-carrying) messages must not duplicate
        again = merge_messages(first, first)
        assert len(again) == 1
        assert again == first

    def test_appends_new_messages(self):
        first = merge_messages([], [{"role": "user", "content": "a"}])
        second = merge_messages(first, [{"role": "assistant", "content": "b"}])
        assert [m["content"] for m in second] == ["a", "b"]


# ── contract: dicts stay valid against the shared schema ─────────────────────

def test_state_round_trips_through_shared_schema():
    merged = merge_messages([], [{"role": "user", "content": "hi"}])
    # The shared contract (messages: list[dict]) must accept the reducer output.
    BaseGTMState(company_id=uuid.uuid4(), user_id=uuid.uuid4(), messages=merged)


# ── end-to-end regression ────────────────────────────────────────────────────

@pytest.fixture
def offline(monkeypatch):
    async def _no_tools(*args, **kwargs):
        return []

    monkeypatch.setattr(mcp_client, "get_mcp_tools", _no_tools)
    monkeypatch.setattr(settings, "openai_api_key", "")


@pytest.mark.asyncio
async def test_graph_run_with_messages_does_not_raise(offline):
    state = GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        messages=[{"role": "user", "content": "Launch our analytics product"}],
        metadata={"content_types": ["cold_email"], "count_per_type": 1},
    )
    # Previously raised ValidationError mid-pipeline.
    result = await graph.ainvoke(state.model_dump())

    assert result["current_agent"] == "brand_alignment"
    assert all(isinstance(m, dict) for m in result["messages"])
    assert len(result["messages"]) == 1  # no duplication across nodes
    assert result["messages"][0]["content"] == "Launch our analytics product"

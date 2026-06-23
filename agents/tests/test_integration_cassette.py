"""End-to-end cassette (record/replay) integration test for the GTM graph.

GitHub issue #19 / PR #20.

The sibling `test_integration_pipeline.py` runs the full pipeline but only via
the nodes' OFFLINE FALLBACKS — it blanks `openai_api_key` so the content node
uses its ColdIQ *template* fallback, and never touches the real LLM path.

This test closes that gap. It drives the SAME research -> strategy -> content ->
brand_alignment graph but forces the content node down its REAL
`ChatOpenAI(...).ainvoke(...)` path, with the OpenAI chat-completions HTTP call
intercepted by `respx` and replayed from a recorded cassette
(`cassettes/openai_chat_content_cold_email.json`). That exercises the real
request-build + `response.content` parse logic deterministically and
network-free.

The cassette body carries a recognisable sentinel string; the test asserts the
sentinel appears in a produced content asset, proving the replayed cassette
(not the template fallback) generated the output. If the real LLM path were not
taken — or the cassette not used — the sentinel would be absent and the test
fails, which is the TDD signal we want.

MCP (Perplexity/etc.) stays stubbed to [] — the research node has its own
offline fallback, and an MCP cassette is out of scope for #19.
"""

import uuid

import pytest
import respx

import agents.app.tools.mcp_client as mcp_client
from agents.app.config import settings
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState
from agents.tests.cassettes import (
    CASSETTE_SENTINEL,
    mount_openai_chat_cassette,
)
from shared.schemas import ContentAsset, ResearchReport


@pytest.fixture
def cassette_pipeline(monkeypatch):
    """Force the content node down its REAL LLM path, replayed from a cassette.

    - MCP tools stubbed to [] (research node uses its offline fallback).
    - A dummy *non-empty* OpenAI key so the content node takes the real
      `llm.ainvoke` path rather than the template fallback.
    - respx intercepts the OpenAI chat-completions endpoint and replays the
      recorded cassette body.

    Yields the respx route so a test can assert it was actually called.
    """

    async def _no_tools(*args, **kwargs):
        return []

    monkeypatch.setattr(mcp_client, "get_mcp_tools", _no_tools)
    # Non-empty key -> content node uses the REAL ChatOpenAI path (not templates).
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    with respx.mock(assert_all_called=False) as router:
        route = mount_openai_chat_cassette(
            router, "openai_chat_content_cold_email"
        )
        yield route


@pytest.mark.asyncio
async def test_pipeline_uses_real_llm_path_from_cassette(cassette_pipeline):
    route = cassette_pipeline

    state = GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        metadata={
            "goal": "Launch our B2B SaaS analytics product",
            "content_types": ["cold_email"],
            "count_per_type": 1,
        },
    )

    result = await graph.ainvoke(state.model_dump())

    # Pipeline ran all the way to the final node.
    assert result["current_agent"] == "brand_alignment"

    # Research stage still produced a schema-valid report (offline fallback).
    report = result["research_report"]
    assert isinstance(report, ResearchReport)

    # Content stage produced assets.
    assets = result["content_assets"]
    assert len(assets) > 0
    assert all(isinstance(a, ContentAsset) for a in assets)

    # The real LLM HTTP path was exercised: respx saw the OpenAI call...
    assert route.called, "OpenAI chat-completions endpoint was never called — " \
        "the content node did not take the real LLM path"

    # ...and the cassette body (not the template fallback) produced the asset.
    bodies = "\n\n".join(a.body for a in assets)
    assert CASSETTE_SENTINEL in bodies, (
        "Cassette sentinel missing from content assets — the asset was produced "
        "by the template fallback, not the replayed real LLM response"
    )

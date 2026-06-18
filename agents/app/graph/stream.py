"""Translate a LangGraph run into an ordered stream of AgentEvents.

The agents service exposes this over SSE at POST /run. The backend SSE
endpoint (PR #14) relays these frames to the browser.

Event order for a successful run:
    agent_start
    agent_progress (one per node entered)
    agent_output   (one per major artifact: research / strategy / content)
    agent_complete (summary of what was produced)
    done

On any failure the stream emits an `error` event and then `done`, so the
client always sees a terminal event.

NOTE: the goal is passed through GTMState.metadata, not messages — driving
the graph via `messages` currently trips the add_messages reducer / list[dict]
coercion mismatch (tracked as a separate follow-up).
"""
from __future__ import annotations

import json
import uuid
from typing import AsyncIterator, Optional

from shared.schemas import AgentEvent, AgentEventType
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState


def format_sse(event: AgentEvent) -> str:
    """Render an AgentEvent as a single SSE frame."""
    payload = event.model_dump(mode="json")  # enum -> value, datetime -> iso
    return f"event: {event.event.value}\ndata: {json.dumps(payload)}\n\n"


def _coerce_uuid(value: Optional[str]) -> uuid.UUID:
    """Accept a string/UUID/None and return a UUID (random when absent)."""
    if isinstance(value, uuid.UUID):
        return value
    if value:
        return uuid.UUID(str(value))
    return uuid.uuid4()


def build_initial_state(
    company_id: Optional[str],
    user_id: Optional[str],
    goal: Optional[str],
    content_types: Optional[list[str]] = None,
    count_per_type: int = 3,
) -> GTMState:
    """Assemble the graph's initial state, driving the goal via metadata."""
    metadata: dict = {"count_per_type": count_per_type}
    if goal:
        metadata["goal"] = goal
    if content_types:
        metadata["content_types"] = content_types
    return GTMState(
        company_id=_coerce_uuid(company_id),
        user_id=_coerce_uuid(user_id),
        metadata=metadata,
    )


async def stream_graph_events(state: GTMState) -> AsyncIterator[AgentEvent]:
    """Run the graph and yield ordered AgentEvents (no SSE formatting)."""
    yield AgentEvent(event=AgentEventType.AGENT_START, message="Pipeline started")

    produced = {"research_report": False, "gtm_strategy": False, "content_assets": 0}
    try:
        async for chunk in graph.astream(state.model_dump(), stream_mode="updates"):
            # `updates` mode: {node_name: {changed state fields}}
            for node, delta in chunk.items():
                yield AgentEvent(
                    event=AgentEventType.AGENT_PROGRESS,
                    agent=node,
                    message=f"{node} complete",
                )
                if not delta:
                    continue
                if delta.get("research_report") is not None and not produced["research_report"]:
                    produced["research_report"] = True
                    yield AgentEvent(
                        event=AgentEventType.AGENT_OUTPUT,
                        agent=node,
                        message="Research report ready",
                    )
                if delta.get("gtm_strategy") is not None and not produced["gtm_strategy"]:
                    produced["gtm_strategy"] = True
                    yield AgentEvent(
                        event=AgentEventType.AGENT_OUTPUT,
                        agent=node,
                        message="GTM strategy ready",
                    )
                assets = delta.get("content_assets")
                if assets:
                    produced["content_assets"] = len(assets)
                    yield AgentEvent(
                        event=AgentEventType.AGENT_OUTPUT,
                        agent=node,
                        message=f"{len(assets)} content asset(s) ready",
                    )
    except Exception as exc:  # noqa: BLE001 — surface any failure as an error event
        yield AgentEvent(
            event=AgentEventType.ERROR,
            message=f"{type(exc).__name__}: {exc}",
        )
        yield AgentEvent(event=AgentEventType.DONE)
        return

    yield AgentEvent(
        event=AgentEventType.AGENT_COMPLETE,
        message="Pipeline complete",
        data=produced,
    )
    yield AgentEvent(event=AgentEventType.DONE)


async def stream_graph_sse(state: GTMState) -> AsyncIterator[str]:
    """Run the graph and yield SSE-formatted frames."""
    async for event in stream_graph_events(state):
        yield format_sse(event)

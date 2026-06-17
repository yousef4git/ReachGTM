"""Backend → agents SSE relay (PR #14).

The backend image does not contain the graph; it reaches the agents service
over HTTP (settings.agents_url) and relays the agents' SSE frames to the
browser. Any failure reaching/!reading the agents stream is surfaced to the
client as an `error` event followed by `done`, so the client always sees a
terminal event.
"""
from __future__ import annotations

import json
from typing import AsyncIterator, Optional
from uuid import UUID

import httpx

from shared.schemas import AgentEvent, AgentEventType
from backend.app.config import settings


def format_sse(event: AgentEvent) -> str:
    """Render an AgentEvent as a single SSE frame."""
    payload = event.model_dump(mode="json")
    return f"event: {event.event.value}\ndata: {json.dumps(payload)}\n\n"


def _error_then_done(message: str) -> list[str]:
    return [
        format_sse(AgentEvent(event=AgentEventType.ERROR, message=message)),
        format_sse(AgentEvent(event=AgentEventType.DONE)),
    ]


async def stream_strategy_events(
    *,
    company_id: Optional[str | UUID],
    user_id: Optional[str | UUID],
    goal: str,
    content_types: Optional[list[str]] = None,
    count_per_type: int = 3,
) -> AsyncIterator[str]:
    """Open a streaming POST to the agents /run endpoint and relay SSE frames."""
    payload = {
        "company_id": str(company_id) if company_id else None,
        "user_id": str(user_id) if user_id else None,
        "goal": goal,
        "content_types": content_types,
        "count_per_type": count_per_type,
    }
    url = f"{settings.agents_url}/run"

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk.decode("utf-8")
    except Exception as exc:  # noqa: BLE001 — any transport/stream failure -> error event
        for frame in _error_then_done(f"agents stream failed: {type(exc).__name__}"):
            yield frame

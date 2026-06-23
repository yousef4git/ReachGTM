"""Backend → agents SSE relay (PR #14).

The backend image does not contain the graph; it reaches the agents service
over HTTP (settings.agents_url) and relays the agents' SSE frames to the
browser. Any failure reaching/!reading the agents stream is surfaced to the
client as an `error` event followed by `done`, so the client always sees a
terminal event.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional
from uuid import UUID

import httpx

from shared.schemas import AgentEvent, AgentEventType
from backend.app.config import settings

logger = logging.getLogger(__name__)


def format_sse(event: AgentEvent) -> str:
    """Render an AgentEvent as a single SSE frame."""
    payload = event.model_dump(mode="json")
    return f"event: {event.event.value}\ndata: {json.dumps(payload)}\n\n"


def _error_then_done(message: str) -> list[str]:
    return [
        format_sse(AgentEvent(event=AgentEventType.ERROR, message=message)),
        format_sse(AgentEvent(event=AgentEventType.DONE)),
    ]


def _parse_frame(frame: str) -> tuple[Optional[str], Optional[dict]]:
    """Pull the event type and parsed JSON data out of one SSE frame."""
    event_type: Optional[str] = None
    data: Optional[dict] = None
    for line in frame.splitlines():
        if line.startswith("event:"):
            event_type = line[len("event:"):].strip()
        elif line.startswith("data:"):
            raw = line[len("data:"):].strip()
            try:
                payload = json.loads(raw)
                data = payload.get("data") if isinstance(payload, dict) else None
            except json.JSONDecodeError:
                data = None
    return event_type, data


async def _persist_bundle(company_id, user_id, bundle: Optional[dict]) -> Optional[dict]:
    """Best-effort persistence of the completed bundle. Never raises."""
    from backend.app.db.connection import get_pool
    from backend.app.services.strategy_service import persist_bundle

    if not bundle or not company_id or not user_id:
        return None
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "SELECT set_config('app.current_company_id', $1, TRUE)", str(company_id)
            )
            return await persist_bundle(conn, company_id, user_id, bundle)
    except Exception as exc:  # noqa: BLE001 — persistence must never break the stream
        logger.warning("bundle persistence failed: %s: %s", type(exc).__name__, exc)
        return None


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

    bundle: Optional[dict] = None
    pending_done: Optional[str] = None
    buffer = ""

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if not chunk:
                        continue
                    buffer += chunk.decode("utf-8")
                    # SSE frames are separated by a blank line.
                    while "\n\n" in buffer:
                        frame, buffer = buffer.split("\n\n", 1)
                        if not frame.strip():
                            continue
                        event_type, data = _parse_frame(frame)
                        if event_type == AgentEventType.AGENT_COMPLETE.value:
                            bundle = data
                        if event_type == AgentEventType.DONE.value:
                            # Hold the terminal frame so persistence + the
                            # `persisted` event land before the client closes.
                            pending_done = frame + "\n\n"
                            continue
                        yield frame + "\n\n"
                # Flush any trailing frame without a blank-line terminator.
                if buffer.strip():
                    event_type, data = _parse_frame(buffer)
                    if event_type == AgentEventType.AGENT_COMPLETE.value:
                        bundle = data
                    if event_type == AgentEventType.DONE.value:
                        pending_done = buffer if buffer.endswith("\n\n") else buffer + "\n\n"
                    else:
                        yield buffer if buffer.endswith("\n\n") else buffer + "\n\n"
    except Exception as exc:  # noqa: BLE001 — any transport/stream failure -> error event
        for frame in _error_then_done(f"agents stream failed: {type(exc).__name__}"):
            yield frame
        return

    persisted = await _persist_bundle(company_id, user_id, bundle)
    if persisted:
        yield format_sse(
            AgentEvent(
                event=AgentEventType.PERSISTED,
                message="Saved to your library",
                data=persisted,
            )
        )

    yield pending_done or format_sse(AgentEvent(event=AgentEventType.DONE))

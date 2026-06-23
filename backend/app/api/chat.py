from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.app.services.agent_stream import stream_strategy_events

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat(request: Request):
    """Stream GTM pipeline agent events as SSE.

    The backend image does not contain the graph; it relays the agents service
    SSE stream over HTTP (see services/agent_stream.py). Auth is enforced by
    TenantMiddleware, which sets request.state.company_id / user_id.
    """
    body = await request.json()

    events = stream_strategy_events(
        company_id=getattr(request.state, "company_id", None),
        user_id=getattr(request.state, "user_id", None),
        goal=body.get("goal"),
        content_types=body.get("content_types"),
        count_per_type=body.get("count_per_type", 3),
    )

    return StreamingResponse(events, media_type="text/event-stream")

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from agents.app.graph.stream import build_initial_state, stream_graph_sse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat(request: Request):
    body = await request.json()

    state = build_initial_state(
        company_id=str(request.state.company_id),
        user_id=str(request.state.user_id),
        goal=body.get("goal"),
        content_types=body.get("content_types"),
        count_per_type=body.get("count_per_type", 3),
    )

    return StreamingResponse(stream_graph_sse(state), media_type="text/event-stream")
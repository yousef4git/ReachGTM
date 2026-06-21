from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid
import asyncpg

from shared.schemas import StrategyGenerateRequest
from backend.app.db.connection import get_db
from backend.app.services.agent_stream import stream_strategy_events
from backend.app.services.strategy_service import (
    create_strategy,
    get_strategy_by_id,
)

router = APIRouter(prefix="/strategy", tags=["strategy"])


class StrategyStreamRequest(BaseModel):
    goal: str
    session_id: str | None = None
    content_types: list[str] | None = None
    count_per_type: int = 3


@router.post("/generate/stream")
async def generate_strategy_stream(body: StrategyStreamRequest, request: Request):
    """Stream GTM pipeline agent events to the client as SSE.

    Auth is enforced by TenantMiddleware, which decodes the JWT and sets
    request.state.company_id / user_id. The goal is forwarded to the agents
    service, which runs the graph and streams AgentEvents back.
    """
    company_id = getattr(request.state, "company_id", None)
    user_id = getattr(request.state, "user_id", None)
    events = stream_strategy_events(
        company_id=company_id,
        user_id=user_id,
        goal=body.goal,
        content_types=body.content_types,
        count_per_type=body.count_per_type,
    )
    return StreamingResponse(events, media_type="text/event-stream")


@router.post("/generate")
async def generate_strategy(
    body: StrategyGenerateRequest,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
):
    strategy = await create_strategy(
        conn=conn,
        company_id=request.state.company_id,
        user_id=request.state.user_id,
        session_id=uuid.uuid4(),
        payload=body.model_dump(),
    )

    return strategy


@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    conn: asyncpg.Connection = Depends(get_db),
):
    strategy = await get_strategy_by_id(conn, strategy_id)

    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return strategy

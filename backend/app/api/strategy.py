from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from jose import jwt, JWTError
from pydantic import BaseModel
import uuid
import asyncpg

from shared.schemas import StrategyGenerateRequest
from backend.app.config import settings
from backend.app.db.connection import get_db
from backend.app.services.agent_stream import stream_strategy_events
from backend.app.services.strategy_service import (
    create_strategy,
    get_strategy_by_id,
    list_strategies,
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


@router.get("/generate/stream")
async def generate_strategy_stream_get(
    token: str = "",
    goal: str = "",
    session_id: str | None = None,
    content_types: str | None = None,
    count_per_type: int = 3,
):
    """GET variant of the SSE stream for the browser EventSource API.

    EventSource is GET-only and cannot set an Authorization header, so the JWT
    arrives as a ?token= query param and is decoded here (TenantMiddleware lets
    this route through via SELF_AUTH_ROUTES). content_types is a comma-separated
    list because query params can't carry a JSON array.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid token"})

    company_id = payload.get("company_id")
    if not company_id:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid token"})

    types_list = [t for t in content_types.split(",") if t] if content_types else None
    events = stream_strategy_events(
        company_id=company_id,
        user_id=payload.get("sub"),
        goal=goal,
        content_types=types_list,
        count_per_type=count_per_type,
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


@router.get("/")
async def list_strategies_endpoint(request: Request):
    """List the company's persisted strategies, newest first.

    Self-acquires a pooled connection so it degrades to [] without an
    authenticated tenant or initialized pool (keeps the route unit-testable)."""
    company_id = getattr(request.state, "company_id", None)
    if not company_id:
        return []
    from backend.app.db.connection import get_pool, set_tenant

    pool = get_pool()
    async with pool.acquire() as conn:
        await set_tenant(conn, company_id)
        return await list_strategies(conn, company_id)


@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: str,
    conn: asyncpg.Connection = Depends(get_db),
):
    strategy = await get_strategy_by_id(conn, strategy_id)

    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return strategy

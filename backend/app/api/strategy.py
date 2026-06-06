from fastapi import APIRouter
from shared.schemas import StrategyGenerateRequest
router = APIRouter(prefix="/strategy", tags=["strategy"])

@router.post("/generate")
async def generate_strategy(body: StrategyGenerateRequest):
    # TODO: Epic 2 PR #14 — triggers LangGraph pipeline, streams SSE events
    return {"status": "not_implemented"}

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    # TODO: Epic 2 PR #17 — fetches strategy from DB
    return {"status": "not_implemented"}

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.analytics_service import calculate_strategy_performance

router = APIRouter(prefix="/analytics", tags=["analytics"])


class StrategyPerformanceRequest(BaseModel):
    sent: int = 0
    opened: int = 0
    replied: int = 0


@router.post("/strategy-performance")
async def get_strategy_performance(body: StrategyPerformanceRequest):
    return calculate_strategy_performance(
        sent=body.sent,
        opened=body.opened,
        replied=body.replied,
    )
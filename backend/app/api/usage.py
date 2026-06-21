from fastapi import APIRouter

from backend.app.services.usage_service import calculate_usage_summary

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary")
async def get_usage_summary():
    return calculate_usage_summary()
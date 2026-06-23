from fastapi import APIRouter

from shared.schemas import ContentGenerateRequest
from backend.app.services.content_service import generate_content_assets

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/generate")
async def generate_content(body: ContentGenerateRequest):
    assets = generate_content_assets(body)

    return {
        "count": len(assets),
        "assets": [asset.model_dump(mode="json") for asset in assets],
    }


@router.get("/")
async def list_content():
    return {
        "count": 0,
        "assets": [],
    }
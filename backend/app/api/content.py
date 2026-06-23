from fastapi import APIRouter, Request

from shared.schemas import ContentGenerateRequest
from backend.app.db.connection import get_pool, set_tenant
from backend.app.services.content_service import generate_content_assets, list_content

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/generate")
async def generate_content(body: ContentGenerateRequest):
    assets = generate_content_assets(body)

    return {
        "count": len(assets),
        "assets": [asset.model_dump(mode="json") for asset in assets],
    }


@router.get("/")
async def list_content_endpoint(request: Request):
    """Return the company's persisted content assets (tenant-scoped via RLS).

    Acquires its own pooled connection (rather than the get_db dependency) so the
    endpoint degrades to an empty list when there is no authenticated tenant or
    no initialized pool — keeping it unit-testable in isolation.
    """
    company_id = getattr(request.state, "company_id", None)
    if not company_id:
        return {"count": 0, "assets": []}

    pool = get_pool()
    async with pool.acquire() as conn:
        await set_tenant(conn, company_id)
        assets = await list_content(conn, company_id)
    return {"count": len(assets), "assets": assets}

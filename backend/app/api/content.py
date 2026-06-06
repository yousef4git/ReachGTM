from fastapi import APIRouter
from shared.schemas import ContentGenerateRequest
router = APIRouter(prefix="/content", tags=["content"])

@router.post("/generate")
async def generate_content(body: ContentGenerateRequest):
    # TODO: Epic 2 PR #18
    return {"status": "not_implemented"}

@router.get("/")
async def list_content():
    # TODO: Epic 2 PR #18
    return {"status": "not_implemented"}

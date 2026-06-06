from fastapi import APIRouter
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat():
    # TODO: Epic 2 PR #14 — SSE streaming from LangGraph
    return {"status": "not_implemented"}

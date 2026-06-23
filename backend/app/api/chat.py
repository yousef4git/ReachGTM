from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import asyncpg

from backend.app.db.connection import get_db
from backend.app.services.chat_service import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


async def _company_name(conn: asyncpg.Connection, company_id) -> str:
    if not company_id:
        return "your company"
    row = await conn.fetchrow("SELECT name FROM companies WHERE id = $1::uuid", str(company_id))
    return row["name"] if row else "your company"


@router.post("/")
async def chat(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    """Grounded company chatbot. Streams an answer (SSE) built from the company's
    knowledge base, GTM strategy, content library, and memory.

    Body: {message: str, history?: [{role, content}]}. Auth via TenantMiddleware
    (Authorization header), which sets request.state.company_id.
    """
    body = await request.json()
    company_id = getattr(request.state, "company_id", None)
    message = (body.get("message") or "").strip()
    history = body.get("history") or []

    if not message:
        async def _empty():
            yield 'event: error\ndata: {"message": "Empty message"}\n\n'
            yield 'event: done\ndata: {}\n\n'

        return StreamingResponse(_empty(), media_type="text/event-stream")

    company_name = await _company_name(conn, company_id)
    events = stream_chat(conn, company_id, company_name, message, history)
    return StreamingResponse(events, media_type="text/event-stream")

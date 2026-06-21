from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
import asyncpg
from backend.app.db.connection import get_db
from backend.app.services.knowledge_service import ingest_document
router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    conn: asyncpg.Connection = Depends(get_db),
):
    company_id = request.state.company_id
    content = await file.read()
    result = await ingest_document(conn, content, file.filename, company_id, doc_type)
    return result

@router.get("/")
async def list_documents(
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
):
    company_id = request.state.company_id
    rows = await conn.fetch(
        """SELECT id, filename, doc_type, status, s3_key, chunk_count, created_at
           FROM knowledge_documents
           WHERE company_id = $1
           ORDER BY created_at DESC""",
        company_id,
    )
    return {"documents": [dict(row) for row in rows]}
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
async def list_documents():
    # TODO: Epic 2
    return {"status": "not_implemented"}

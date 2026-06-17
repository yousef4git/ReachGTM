import io
import uuid
import asyncpg
from openai import AsyncOpenAI
from pypdf import PdfReader
from docx import Document as DocxDocument
from backend.app.config import settings
from backend.app.services.storage_service import upload_object

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


def _storage_key(company_id: str, doc_id: uuid.UUID, filename: str) -> str:
    """Tenant-scoped object key for a raw uploaded document."""
    return f"{company_id}/{doc_id}/{filename}"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

def _extract_text(content: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif filename.lower().endswith((".docx", ".doc")):
        doc = DocxDocument(io.BytesIO(content))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    raise ValueError(f"Unsupported file type: {filename}")

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_words: list[str] = []

    for para in paragraphs:
        words = para.split()
        if len(current_words) + len(words) > chunk_size:
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = current_words[-overlap:]
        current_words.extend(words)

    if current_words:
        chunks.append(" ".join(current_words))
    return chunks

async def _embed_texts(texts: list[str]) -> list[list[float]]:
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]

async def ingest_document(
    conn: asyncpg.Connection,
    content: bytes,
    filename: str,
    company_id: str,
    doc_type: str,
) -> dict:
    doc_id = uuid.uuid4()
    namespace = f"{company_id}:{doc_type}"

    # Persist the raw file to object storage when configured (skipped in local
    # dev where no bucket is set). The key is stored for later retrieval.
    s3_key = None
    if settings.s3_bucket_name:
        s3_key = _storage_key(company_id, doc_id, filename)
        await upload_object(content, s3_key)

    await conn.execute(
        """INSERT INTO knowledge_documents (id, company_id, filename, doc_type, status, s3_key)
           VALUES ($1, $2, $3, $4, 'pending', $5)""",
        doc_id, uuid.UUID(company_id), filename, doc_type, s3_key,
    )

    try:
        text = _extract_text(content, filename)
        chunks = _chunk_text(text)
        embeddings = await _embed_texts(chunks)

        async with conn.transaction():
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                await conn.execute(
                    """INSERT INTO document_chunks
                       (document_id, company_id, namespace, chunk_index, content, embedding)
                       VALUES ($1, $2, $3, $4, $5, $6::vector)""",
                    doc_id, uuid.UUID(company_id), namespace, i, chunk, str(embedding),
                )
            await conn.execute(
                "UPDATE knowledge_documents SET status='indexed', chunk_count=$1 WHERE id=$2",
                len(chunks), doc_id,
            )

        return {"document_id": str(doc_id), "chunks": len(chunks), "status": "indexed"}

    except Exception as exc:
        await conn.execute(
            "UPDATE knowledge_documents SET status='failed' WHERE id=$1", doc_id
        )
        raise exc

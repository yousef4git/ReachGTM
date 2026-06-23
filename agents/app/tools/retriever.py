from abc import ABC, abstractmethod
import asyncpg
from openai import AsyncOpenAI
from agents.app.config import settings

# Lazily instantiated: creating the client eagerly at import time raises when no
# API key is configured (e.g. offline unit tests), so defer it until first use.
_openai_client: AsyncOpenAI | None = None


def _client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client

class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, namespace: str, top_k: int = 5) -> list[dict]:
        ...

class PgVectorRetriever(Retriever):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def retrieve(self, query: str, namespace: str, top_k: int = 5) -> list[dict]:
        """Vector-search the company's knowledge chunks.

        `namespace` is the company_id. Ingestion stores chunks under
        namespace="{company_id}:{doc_type}", so we match on the indexed
        company_id column (a prefix match on namespace returned 0 rows — that
        mismatch is why RAG was previously dead). RLS is bypassed by the
        service role, so we scope explicitly by company_id here.
        """
        response = await _client().embeddings.create(
            model="text-embedding-3-small",
            input=[query],
        )
        query_embedding = response.data[0].embedding

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT content, metadata,
                          1 - (embedding <=> $1::vector) AS similarity
                   FROM document_chunks
                   WHERE company_id = $2::uuid
                   ORDER BY embedding <=> $1::vector
                   LIMIT $3""",
                str(query_embedding), str(namespace), top_k,
            )
        return [
            {"content": r["content"], "metadata": dict(r["metadata"]), "similarity": r["similarity"]}
            for r in rows
        ]

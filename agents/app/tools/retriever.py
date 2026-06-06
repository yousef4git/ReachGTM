from abc import ABC, abstractmethod
import asyncpg
from openai import AsyncOpenAI
from agents.app.config import settings

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, namespace: str, top_k: int = 5) -> list[dict]:
        ...

class PgVectorRetriever(Retriever):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def retrieve(self, query: str, namespace: str, top_k: int = 5) -> list[dict]:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[query],
        )
        query_embedding = response.data[0].embedding

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT content, metadata,
                          1 - (embedding <=> $1::vector) AS similarity
                   FROM document_chunks
                   WHERE namespace = $2
                   ORDER BY embedding <=> $1::vector
                   LIMIT $3""",
                str(query_embedding), namespace, top_k,
            )
        return [
            {"content": r["content"], "metadata": dict(r["metadata"]), "similarity": r["similarity"]}
            for r in rows
        ]

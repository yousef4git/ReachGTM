"""Grounded company chatbot (RAG).

Answers questions using everything the company has produced: its knowledge base
(vector search over document_chunks), its latest generated GTM strategy, its
recent content library, and its company memory. Streams tokens from
`settings.chat_model` (gpt-5.4-mini) as SSE.
"""
from __future__ import annotations

import json
import uuid
from typing import AsyncIterator, Optional

import asyncpg
from openai import AsyncOpenAI

from backend.app.config import settings

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

EMBED_MODEL = "text-embedding-3-small"
TOP_K = 6
MAX_HISTORY = 8


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _retrieve_kb(conn: asyncpg.Connection, company_id: uuid.UUID, query: str) -> list[dict]:
    resp = await openai_client.embeddings.create(model=EMBED_MODEL, input=[query])
    embedding = resp.data[0].embedding
    rows = await conn.fetch(
        """SELECT dc.content,
                  kd.filename,
                  kd.doc_type,
                  1 - (dc.embedding <=> $1::vector) AS similarity
           FROM document_chunks dc
           JOIN knowledge_documents kd ON kd.id = dc.document_id
           WHERE dc.company_id = $2
           ORDER BY dc.embedding <=> $1::vector
           LIMIT $3""",
        str(embedding), company_id, TOP_K,
    )
    return [
        {
            "content": r["content"],
            "filename": r["filename"],
            "doc_type": r["doc_type"],
            "similarity": float(r["similarity"]),
        }
        for r in rows
    ]


async def _latest_strategy(conn: asyncpg.Connection, company_id: uuid.UUID) -> Optional[dict]:
    row = await conn.fetchrow(
        """SELECT payload FROM strategies
           WHERE company_id = $1 AND status = 'completed'
           ORDER BY created_at DESC LIMIT 1""",
        company_id,
    )
    if not row or row["payload"] is None:
        return None
    payload = row["payload"]
    return json.loads(payload) if isinstance(payload, str) else dict(payload)


async def _recent_content(conn: asyncpg.Connection, company_id: uuid.UUID) -> list[dict]:
    rows = await conn.fetch(
        """SELECT content_type, title FROM content_assets
           WHERE company_id = $1 ORDER BY created_at DESC LIMIT 10""",
        company_id,
    )
    return [{"type": r["content_type"], "title": r["title"]} for r in rows]


async def _memory(conn: asyncpg.Connection, company_id: uuid.UUID) -> list[dict]:
    rows = await conn.fetch(
        "SELECT key, value FROM company_memory WHERE company_id = $1", company_id
    )
    out = []
    for r in rows:
        val = r["value"]
        out.append({"key": r["key"], "value": json.loads(val) if isinstance(val, str) else val})
    return out


def _summarize_strategy(strategy: Optional[dict]) -> str:
    if not strategy:
        return "No GTM strategy has been generated yet."
    gtm = strategy.get("gtm_strategy") or {}
    if not gtm:
        return "No GTM strategy has been generated yet."
    parts: list[str] = []
    if gtm.get("positioning_statement"):
        parts.append(f"Positioning: {gtm['positioning_statement']}")
    if gtm.get("motion"):
        parts.append(f"GTM motion: {gtm['motion']}")
    vp = gtm.get("value_proposition") or {}
    if vp.get("headline"):
        parts.append(f"Value prop: {vp['headline']} — {vp.get('subheadline', '')}")
    icp = gtm.get("icp") or {}
    if icp.get("title"):
        parts.append(
            f"ICP: {icp.get('title')} in {icp.get('industry', '')} "
            f"({icp.get('company_size', '')}); pains: {', '.join(icp.get('pain_points', [])[:3])}"
        )
    channels = gtm.get("channels") or []
    if channels:
        ch = ", ".join(
            f"{c.get('name')} (P{c.get('priority')})" for c in sorted(channels, key=lambda x: x.get("priority", 99))[:5]
        )
        parts.append(f"Channels: {ch}")
    research = strategy.get("research_report") or {}
    comps = research.get("competitors") or []
    if comps:
        parts.append("Competitors: " + ", ".join(c.get("name", "") for c in comps[:5]))
    return "\n".join(parts)


def _build_messages(
    question: str,
    history: list[dict],
    company_name: str,
    kb_chunks: list[dict],
    strategy: Optional[dict],
    content: list[dict],
    memory: list[dict],
) -> list[dict]:
    kb_text = (
        "\n\n".join(
            f"[{i+1}] ({c['doc_type']} · {c['filename']})\n{c['content'][:900]}"
            for i, c in enumerate(kb_chunks)
        )
        or "No knowledge base documents matched this question."
    )
    content_text = (
        "\n".join(f"- {c['type']}: {c['title']}" for c in content)
        or "No content assets generated yet."
    )
    memory_text = (
        "\n".join(f"- {m['key']}: {json.dumps(m['value'])[:300]}" for m in memory)
        or "No saved company memory."
    )

    system = (
        f"You are the in-house GTM strategist assistant for {company_name}. "
        "Answer the user's question grounded ONLY in the company context provided below "
        "(knowledge base, GTM strategy, content library, and memory). "
        "Be concrete, specific, and actionable — you are talking to the company's own team. "
        "When you use a knowledge-base fact, cite it inline like [1], [2] using the numbered sources. "
        "If the context does not contain the answer, say so plainly and suggest what to upload or generate. "
        "Never invent competitors, metrics, or facts that aren't in the context.\n\n"
        f"=== GTM STRATEGY ===\n{_summarize_strategy(strategy)}\n\n"
        f"=== CONTENT LIBRARY ===\n{content_text}\n\n"
        f"=== COMPANY MEMORY ===\n{memory_text}\n\n"
        f"=== KNOWLEDGE BASE (numbered sources) ===\n{kb_text}"
    )

    messages = [{"role": "system", "content": system}]
    for turn in history[-MAX_HISTORY:]:
        role = turn.get("role")
        if role in ("user", "assistant") and turn.get("content"):
            messages.append({"role": role, "content": str(turn["content"])})
    messages.append({"role": "user", "content": question})
    return messages


async def stream_chat(
    conn: asyncpg.Connection,
    company_id,
    company_name: str,
    question: str,
    history: list[dict],
) -> AsyncIterator[str]:
    """Yield SSE frames: token* → sources → done (or error → done)."""
    cid = _as_uuid(company_id)
    try:
        kb_chunks = await _retrieve_kb(conn, cid, question)
        strategy = await _latest_strategy(conn, cid)
        content = await _recent_content(conn, cid)
        memory = await _memory(conn, cid)
        messages = _build_messages(
            question, history, company_name, kb_chunks, strategy, content, memory
        )

        stream = await openai_client.chat.completions.create(
            model=settings.chat_model,
            messages=messages,
            stream=True,
            temperature=0.3,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield _sse("token", {"text": delta})

        sources = [
            {"filename": c["filename"], "doc_type": c["doc_type"], "similarity": round(c["similarity"], 3)}
            for c in kb_chunks
        ]
        yield _sse(
            "sources",
            {
                "sources": sources,
                "grounded": {
                    "kb_chunks": len(kb_chunks),
                    "has_strategy": strategy is not None,
                    "content_assets": len(content),
                    "memory_keys": len(memory),
                },
            },
        )
    except Exception as exc:  # noqa: BLE001 — surface a clean error to the client
        yield _sse("error", {"message": f"{type(exc).__name__}: {exc}"})
    finally:
        yield _sse("done", {})

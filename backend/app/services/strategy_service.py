import json
import uuid

import asyncpg

from backend.app.services.content_service import persist_content_assets


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


async def create_strategy(
    conn: asyncpg.Connection,
    company_id,
    user_id,
    session_id,
    payload,
):
    # asyncpg does not auto-encode dicts to JSONB — serialize and cast,
    # mirroring memory_service's convention for JSONB columns.
    row = await conn.fetchrow(
        """
        INSERT INTO strategies (
            company_id,
            user_id,
            session_id,
            status,
            payload
        )
        VALUES ($1, $2, $3, 'completed', $4::jsonb)
        RETURNING *
        """,
        company_id,
        user_id,
        session_id,
        json.dumps(payload),
    )
    return _row_to_strategy(row)


async def get_strategy_by_id(
    conn: asyncpg.Connection,
    strategy_id,
):
    row = await conn.fetchrow(
        """
        SELECT *
        FROM strategies
        WHERE id = $1
        """,
        strategy_id,
    )

    if row is None:
        return None

    return _row_to_strategy(row)


async def persist_bundle(
    conn: asyncpg.Connection,
    company_id,
    user_id,
    bundle: dict,
) -> dict:
    """Persist a completed agent bundle: one `strategies` row holding the full
    bundle payload, plus one `content_assets` row per generated asset.

    Returns {strategy_id, content_ids} for the `persisted` SSE event.
    """
    company_uuid = _as_uuid(company_id)
    user_uuid = _as_uuid(user_id)
    session_id = uuid.uuid4()

    assets = bundle.get("content_assets") or []
    payload = {
        "gtm_strategy": bundle.get("gtm_strategy"),
        "research_report": bundle.get("research_report"),
        "content_assets": assets,
    }

    async with conn.transaction():
        strategy_id = await conn.fetchval(
            """INSERT INTO strategies (company_id, user_id, session_id, status, payload)
               VALUES ($1, $2, $3, 'completed', $4::jsonb)
               RETURNING id""",
            company_uuid,
            user_uuid,
            session_id,
            json.dumps(payload),
        )
        content_ids = await persist_content_assets(conn, company_uuid, strategy_id, assets)

    return {"strategy_id": str(strategy_id), "content_ids": content_ids}


async def list_strategies(conn: asyncpg.Connection, company_id) -> list[dict]:
    """Return the company's strategies (newest first) with their bundle payload."""
    rows = await conn.fetch(
        """SELECT id, status, payload, created_at
           FROM strategies
           WHERE company_id = $1
           ORDER BY created_at DESC""",
        _as_uuid(company_id),
    )
    out: list[dict] = []
    for row in rows:
        item = _row_to_strategy(row)
        item["id"] = str(item["id"])
        if item.get("created_at") is not None:
            item["created_at"] = item["created_at"].isoformat()
        out.append(item)
    return out


def _row_to_strategy(row: asyncpg.Record) -> dict:
    """Convert a strategies row to a dict, decoding the JSONB payload (which
    asyncpg returns as a JSON string in the absence of a type codec)."""
    strategy = dict(row)
    payload = strategy.get("payload")
    if isinstance(payload, str):
        strategy["payload"] = json.loads(payload)
    return strategy
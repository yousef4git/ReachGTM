"""Long-term company memory (Epic 4 — Phase 2).

Persists key/value facts across sessions in the `company_memory` table
(JSONB values, UNIQUE per (company_id, key)). All operations run on a
tenant-scoped asyncpg connection (get_db sets app.current_company_id), so RLS
enforces isolation; company_id is also passed explicitly for the INSERT.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import asyncpg


def _as_uuid(company_id: str | UUID) -> UUID:
    return company_id if isinstance(company_id, UUID) else UUID(str(company_id))


def _load(value: Any) -> Any:
    """asyncpg returns JSONB as a string by default; decode it."""
    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)):
        return json.loads(value)
    return value  # already decoded (custom codec)


async def remember(conn: asyncpg.Connection, company_id: str | UUID, key: str, value: Any) -> None:
    """Upsert a fact. Overwrites the value (and bumps updated_at) on conflict."""
    await conn.execute(
        """INSERT INTO company_memory (company_id, key, value)
           VALUES ($1, $2, $3::jsonb)
           ON CONFLICT (company_id, key)
           DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()""",
        _as_uuid(company_id), key, json.dumps(value),
    )


async def recall(conn: asyncpg.Connection, company_id: str | UUID, key: str) -> Any:
    """Return the stored value for `key`, or None if not present."""
    value = await conn.fetchval(
        "SELECT value FROM company_memory WHERE company_id = $1 AND key = $2",
        _as_uuid(company_id), key,
    )
    return _load(value)


async def recall_all(conn: asyncpg.Connection, company_id: str | UUID) -> dict[str, Any]:
    """Return all stored facts for the company as a {key: value} dict."""
    rows = await conn.fetch(
        "SELECT key, value FROM company_memory WHERE company_id = $1 ORDER BY key",
        _as_uuid(company_id),
    )
    return {row["key"]: _load(row["value"]) for row in rows}


async def forget(conn: asyncpg.Connection, company_id: str | UUID, key: str) -> bool:
    """Delete a fact. Returns True if a row was removed."""
    status = await conn.execute(
        "DELETE FROM company_memory WHERE company_id = $1 AND key = $2",
        _as_uuid(company_id), key,
    )
    return status != "DELETE 0"

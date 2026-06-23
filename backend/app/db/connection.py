import asyncpg
from fastapi import Request
from backend.app.config import settings

_pool: asyncpg.Pool | None = None

async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=60,
    )

async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()

def get_pool() -> asyncpg.Pool:
    """Return the live connection pool (for code outside the request/DI cycle,
    e.g. the SSE relay that persists the agent bundle after streaming)."""
    assert _pool is not None, "Database pool not initialized — call init_pool() first"
    return _pool

async def set_tenant(conn: asyncpg.Connection, company_id) -> None:
    """Set the RLS tenant context on a connection for the current request."""
    if company_id:
        await conn.execute(
            "SELECT set_config('app.current_company_id', $1, TRUE)", str(company_id)
        )

async def get_db(request: Request):
    """FastAPI dependency — yields an asyncpg connection from the pool."""
    assert _pool is not None, "Database pool not initialized — call init_pool() first"
    async with _pool.acquire() as conn:
        await set_tenant(conn, getattr(request.state, "company_id", None))
        yield conn

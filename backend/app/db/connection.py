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

async def get_db(request: Request):
    """FastAPI dependency — yields an asyncpg connection from the pool."""
    async with _pool.acquire() as conn:
        company_id = getattr(request.state, "company_id", None)
        if company_id:
            await conn.execute(
                "SELECT set_config('app.current_company_id', $1, TRUE)", company_id
            )
        yield conn

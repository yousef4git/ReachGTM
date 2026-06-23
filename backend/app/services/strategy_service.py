import asyncpg


async def create_strategy(
    conn: asyncpg.Connection,
    company_id,
    user_id,
    session_id,
    payload,
):
    row = await conn.fetchrow(
        """
        INSERT INTO strategies (
            company_id,
            user_id,
            session_id,
            status,
            payload
        )
        VALUES ($1, $2, $3, 'completed', $4)
        RETURNING *
        """,
        company_id,
        user_id,
        session_id,
        payload,
    )
    return dict(row)


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

    return dict(row)
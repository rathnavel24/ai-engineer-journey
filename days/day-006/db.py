"""Day 6: asyncpg connection pool and a single insert_request() helper for
the requests table LoggingMiddleware logs every /chat call to.
"""

import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/postgres")

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Lazily create the pool on first use, then reuse it for every call."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def insert_request(
    *,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    ttfb_ms: float,
    latency_ms: float,
    cost_usd: float,
) -> None:
    """Insert one row recording a completed /chat request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO requests
                (provider, model, prompt_tokens, completion_tokens, ttfb_ms, latency_ms, cost_usd)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            provider,
            model,
            prompt_tokens,
            completion_tokens,
            ttfb_ms,
            latency_ms,
            cost_usd,
        )

"""PostgreSQL connection pool management — delegates to shared_python.DatabasePool.

Maintains backward-compatible module-level exports (init_db, close_db,
get_db, get_pool, transaction, check_health) so existing IPAM code
doesn't need import changes.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from asyncpg import Pool

from shared_python import DatabasePool

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Canonical DatabasePool instance — imported by main.py for app_factory
db_pool = DatabasePool(
    dsn=str(settings.postgres_url),
    schema="ipam,shared,public",
    min_size=settings.db_pool_min,
    max_size=settings.db_pool_max,
    command_timeout=60,
    max_retries=5,
    retry_delay=2.0,
)


async def init_db() -> None:
    """Initialize the database connection pool with retry/backoff."""
    await db_pool.init()


async def close_db() -> None:
    """Close the database connection pool."""
    await db_pool.close()


def get_pool() -> Pool:
    """Get the raw asyncpg pool."""
    return db_pool.pool


@asynccontextmanager
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool."""
    async with db_pool.acquire() as connection:
        yield connection


@asynccontextmanager
async def transaction() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection with an active transaction."""
    async with db_pool.transaction() as connection:
        yield connection


async def check_health() -> bool:
    """Check database connectivity."""
    return await db_pool.check_health()

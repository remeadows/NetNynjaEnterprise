"""PostgreSQL connection pool with retry/backoff on startup.

Fixes SYSLOG-001 root cause: services crash on asyncpg.CannotConnectNowError
if Postgres isn't ready when the container starts. Now retries with exponential
backoff before giving up.

Usage:
    from shared_python import DatabasePool

    db = DatabasePool(
        dsn="postgresql://...",
        schema="ipam,shared,public",
        min_size=5,
        max_size=20,
    )
    await db.init()            # retries up to max_retries
    async with db.acquire() as conn:
        await conn.fetchval("SELECT 1")
    async with db.transaction() as conn:
        await conn.execute("INSERT INTO ...")
    await db.close()
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from asyncpg import Pool

from .logging import get_logger

logger = get_logger(__name__)


class DatabasePool:
    """Managed asyncpg pool with startup retry and health checks.

    Args:
        dsn: PostgreSQL connection string.
        schema: Search path (e.g. "ipam,shared,public").
        min_size: Minimum pool connections.
        max_size: Maximum pool connections.
        command_timeout: Default query timeout in seconds.
        max_retries: Number of connection attempts on startup.
        retry_delay: Initial delay between retries (doubles each attempt).
    """

    def __init__(
        self,
        dsn: str,
        schema: str = "public",
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: int = 60,
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ) -> None:
        self._dsn = dsn
        self._schema = schema
        self._min_size = min_size
        self._max_size = max_size
        self._command_timeout = command_timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._pool: Pool | None = None

    async def init(self) -> None:
        """Initialize the connection pool with retry/backoff.

        Retries on CannotConnectNowError, ConnectionRefusedError,
        and OSError (common Docker startup race conditions).
        """
        if self._pool is not None:
            return

        safe_dsn = self._dsn.split("@")[-1] if "@" in self._dsn else "(hidden)"
        logger.info("initializing_database_pool", target=safe_dsn, schema=self._schema)

        delay = self._retry_delay
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                self._pool = await asyncpg.create_pool(
                    self._dsn,
                    min_size=self._min_size,
                    max_size=self._max_size,
                    command_timeout=self._command_timeout,
                    server_settings={"search_path": self._schema},
                )
                logger.info(
                    "database_pool_initialized",
                    min_size=self._min_size,
                    max_size=self._max_size,
                    attempt=attempt,
                )
                return
            except (
                asyncpg.CannotConnectNowError,
                ConnectionRefusedError,
                OSError,
            ) as e:
                last_error = e
                logger.warning(
                    "database_connection_retry",
                    attempt=attempt,
                    max_retries=self._max_retries,
                    delay=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)  # cap at 30s

        raise ConnectionError(
            f"Failed to connect to database after {self._max_retries} attempts: {last_error}"
        )

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is None:
            return
        logger.info("closing_database_pool")
        await self._pool.close()
        self._pool = None

    @property
    def pool(self) -> Pool:
        """Get the raw pool. Raises RuntimeError if not initialized."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call init() first.")
        return self._pool

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection from the pool."""
        async with self.pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection with an active transaction."""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection

    async def check_health(self) -> bool:
        """Check database connectivity. Returns False on failure."""
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False

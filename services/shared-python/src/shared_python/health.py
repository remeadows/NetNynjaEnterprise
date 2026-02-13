"""Health check endpoint factory.

Creates a standard set of health endpoints (/healthz, /livez, /readyz)
that every Python service exposes. The readyz probe runs caller-supplied
dependency checks (database, NATS, Redis, etc.).

Usage:
    from shared_python import create_health_router, DatabasePool

    db = DatabasePool(...)
    health_router = create_health_router(
        service_name="ipam",
        checks={"database": db.check_health},
    )
    app.include_router(health_router)
"""

from typing import Awaitable, Callable

from fastapi import APIRouter, Response, status


# Type alias for async health check callables
HealthCheck = Callable[[], Awaitable[bool]]


def create_health_router(
    service_name: str,
    checks: dict[str, HealthCheck] | None = None,
) -> APIRouter:
    """Create a health-check router with standard K8s probe endpoints.

    Args:
        service_name: Identifier returned in /healthz (e.g. "ipam").
        checks: Map of dependency name → async bool callable for /readyz.
    """
    router = APIRouter(tags=["Health"])
    _checks = checks or {}

    @router.get("/healthz")
    async def healthz() -> dict:
        """Basic liveness check."""
        return {"status": "ok", "service": service_name}

    @router.get("/livez")
    async def livez() -> dict:
        """Kubernetes liveness probe."""
        return {"status": "ok"}

    @router.get("/readyz")
    async def readyz(response: Response) -> dict:
        """Kubernetes readiness probe — checks all dependencies."""
        results: dict[str, bool] = {}
        for name, check_fn in _checks.items():
            try:
                results[name] = await check_fn()
            except Exception:
                results[name] = False

        all_healthy = all(results.values()) if results else True

        if not all_healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "ready" if all_healthy else "not_ready",
            "checks": results,
        }

    return router

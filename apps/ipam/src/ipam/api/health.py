"""Health check endpoints."""

from fastapi import APIRouter, Response, status

from ..db.connection import check_health as check_db_health

health_router = APIRouter(tags=["Health"])


@health_router.get("/healthz")
async def healthz() -> dict:
    """Basic liveness check."""
    return {"status": "ok", "service": "ipam"}


@health_router.get("/livez")
async def livez() -> dict:
    """Kubernetes liveness probe."""
    return {"status": "ok"}


@health_router.get("/readyz")
async def readyz(response: Response) -> dict:
    """Kubernetes readiness probe - checks all dependencies."""
    checks = {
        "database": await check_db_health(),
    }

    all_healthy = all(checks.values())

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }

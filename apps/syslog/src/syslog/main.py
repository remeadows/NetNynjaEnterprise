"""Syslog service main application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    print(f"Starting Syslog Service on port {settings.SYSLOG_PORT}")

    yield

    # Shutdown
    print("Shutting down Syslog Service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="NetNynja Syslog Service",
        description="Centralized syslog collection and forwarding",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            service="syslog",
            version="0.1.0",
        )

    @app.get("/livez")
    async def liveness() -> dict:
        """Kubernetes liveness probe."""
        return {"status": "ok"}

    @app.get("/readyz")
    async def readiness() -> dict:
        """Kubernetes readiness probe."""
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "syslog.main:app",
        host=settings.SYSLOG_HOST,
        port=settings.SYSLOG_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )

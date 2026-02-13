"""IPAM service configuration.

Extends BaseServiceSettings from shared_python with IPAM-specific fields.
All common infrastructure fields (DB, Redis, NATS, JWT, observability)
are inherited from the shared base class.
"""

from functools import lru_cache

from pydantic import Field

from shared_python import BaseServiceSettings


class Settings(BaseServiceSettings):
    """IPAM-specific settings. Inherits all infra fields from BaseServiceSettings."""

    # Override host/port with IPAM-specific env vars
    host: str = Field(default="0.0.0.0", alias="IPAM_HOST")
    port: int = Field(default=3003, alias="IPAM_PORT")

    # IPAM-specific: OTEL service name
    otel_service_name: str = Field(default="ipam-service", alias="OTEL_SERVICE_NAME")

    # Scanning
    scan_timeout: int = Field(default=300, alias="SCAN_TIMEOUT")
    scan_concurrency: int = Field(default=50, alias="SCAN_CONCURRENCY")
    ping_timeout: float = Field(default=1.0, alias="PING_TIMEOUT")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

"""Base configuration for all Python services.

Provides common infrastructure settings (DB, Redis, NATS, JWT, observability).
Each service subclasses BaseServiceSettings and adds domain-specific fields.

Usage:
    from shared_python import BaseServiceSettings

    class Settings(BaseServiceSettings):
        # Service-specific fields
        scan_timeout: int = Field(default=300, alias="SCAN_TIMEOUT")

        class Config:
            # Override host/port aliases per service
            pass
"""

from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Common settings shared across all Python backend services.

    Subclass this and add service-specific fields. Override host/port
    Field aliases to use service-specific env vars (e.g. IPAM_HOST).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server — subclasses should override alias to SERVICE_HOST / SERVICE_PORT
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    environment: Literal["development", "production", "test"] = Field(
        default="development", alias="NODE_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")

    # Database
    postgres_url: PostgresDsn = Field(..., alias="POSTGRES_URL")
    db_pool_min: int = Field(default=5, alias="DB_POOL_MIN")
    db_pool_max: int = Field(default=20, alias="DB_POOL_MAX")

    # Redis
    redis_url: RedisDsn = Field(..., alias="REDIS_URL")

    # NATS
    nats_url: str = Field(default="nats://localhost:4222", alias="NATS_URL")
    nats_user: str | None = Field(default=None, alias="NATS_USER")
    nats_password: str | None = Field(default=None, alias="NATS_PASSWORD")
    nats_tls_enabled: bool = Field(default=False, alias="NATS_TLS_ENABLED")
    nats_tls_ca: str | None = Field(default=None, alias="NATS_TLS_CA")

    # JWT
    jwt_secret: str | None = Field(default=None, alias="JWT_SECRET")
    jwt_public_key: str | None = Field(default=None, alias="JWT_PUBLIC_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    # VictoriaMetrics
    victoria_url: str = Field(
        default="http://localhost:8428", alias="VICTORIA_METRICS_URL"
    )

    # Observability
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="service", alias="OTEL_SERVICE_NAME")
    jaeger_endpoint: str | None = Field(default=None, alias="JAEGER_ENDPOINT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

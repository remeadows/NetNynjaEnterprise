"""Structured logging configuration — delegates to shared_python.

Maintains backward-compatible imports for the IPAM service.
The IPAM-specific configure_logging() reads settings.log_level and
settings.is_development automatically so callers don't need to pass args.
"""

from shared_python import (
    configure_logging as _configure_logging,
    get_logger,
    bind_context,
    clear_context,
)

from .config import settings

__all__ = ["configure_logging", "get_logger", "bind_context", "clear_context"]


def configure_logging() -> None:
    """Configure logging using IPAM settings."""
    _configure_logging(
        log_level=settings.log_level,
        is_development=settings.is_development,
    )

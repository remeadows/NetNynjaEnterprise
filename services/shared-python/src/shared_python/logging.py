"""Structured logging configuration.

Provides a single configure_logging() call that sets up structlog
with dev console or production JSON output based on environment.

Usage:
    from shared_python import configure_logging, get_logger

    configure_logging(log_level="INFO", is_development=True)
    logger = get_logger(__name__)
    logger.info("service_started", port=8000)
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def configure_logging(
    log_level: str = "INFO",
    is_development: bool = True,
) -> None:
    """Configure structured logging with structlog.

    Args:
        log_level: Python log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        is_development: If True, use colored console output; else JSON for Loki.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_development:
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )

    # Route stdlib logging through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables for all subsequent log calls in this task."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()

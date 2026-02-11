"""
Syslog UDP/TCP collector service.

Listens on UDP/TCP port 514 (configurable) and processes incoming syslog messages.

Security controls (SEC-015):
- Message size cap (SYSLOG_MAX_MESSAGE_SIZE)
- Global and per-source rate limiting
- Optional IP allowlist (SYSLOG_ALLOWED_SOURCES)
- Backpressure when in-memory buffer exceeds threshold
- Structured metrics for all drop events
"""

import asyncio
import ipaddress
import json
import re
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import uuid4

import asyncpg
import structlog
from nats.aio.client import Client as NATSClient

from .config import settings
from .parser import parse_syslog_message, ParsedSyslogMessage

logger = structlog.get_logger()


class SyslogCollector:
    """
    Syslog collector that listens on UDP 514.

    Features:
    - UDP and TCP syslog reception
    - Device and event type parsing
    - Database storage with 10GB circular buffer management
    - Real-time streaming via NATS JetStream
    """

    def __init__(self) -> None:
        self.db_pool: asyncpg.Pool | None = None
        self.nats: NATSClient | None = None
        self.udp_transport: asyncio.DatagramTransport | None = None
        self.running = False
        self.buffer_check_interval = 300  # Check buffer every 5 minutes
        self.batch_size = 100  # Batch insert size
        self.event_buffer: list[dict[str, Any]] = []
        self.buffer_lock = asyncio.Lock()

        # --- SEC-015: Security controls ---

        # IP allowlist (parsed from comma-separated CIDRs/IPs)
        self._allowed_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        self._ip_allowlist_enabled = False
        self._parse_allowed_sources()

        # Rate limiting state (sliding window, resets every second)
        self._global_msg_count = 0
        self._global_window_start = time.monotonic()
        self._per_source_counts: dict[str, int] = defaultdict(int)
        self._per_source_window_start: dict[str, float] = defaultdict(time.monotonic)

        # Drop metrics (reset periodically by metrics reporter)
        self._drops_oversized = 0
        self._drops_rate_limited = 0
        self._drops_ip_denied = 0
        self._drops_backpressure = 0
        self._total_accepted = 0

        # --- SEC-023: Payload redaction patterns ---
        self._redaction_patterns: list[re.Pattern[str]] = []
        self._parse_redaction_patterns()

    def _parse_allowed_sources(self) -> None:
        """Parse SYSLOG_ALLOWED_SOURCES into a list of IP networks."""
        raw = settings.SYSLOG_ALLOWED_SOURCES.strip()
        if not raw:
            self._ip_allowlist_enabled = False
            return

        self._ip_allowlist_enabled = True
        for entry in raw.split(","):
            entry = entry.strip()
            if not entry:
                continue
            try:
                # Handles both "10.0.0.1" and "10.0.0.0/8"
                network = ipaddress.ip_network(entry, strict=False)
                self._allowed_networks.append(network)
            except ValueError:
                logger.warning(
                    "invalid_allowed_source_entry",
                    entry=entry,
                    reason="Could not parse as IP address or CIDR range — skipping.",
                )

        if not self._allowed_networks:
            logger.warning(
                "allowed_sources_configured_but_empty",
                reason="SYSLOG_ALLOWED_SOURCES was set but contained no valid entries. "
                       "All traffic will be DENIED.",
            )

    def _is_source_allowed(self, source_ip: str) -> bool:
        """Check if a source IP is in the allowlist.

        Returns True if allowlist is disabled (empty config) or IP matches.
        """
        if not self._ip_allowlist_enabled:
            return True

        try:
            addr = ipaddress.ip_address(source_ip)
        except ValueError:
            return False

        return any(addr in network for network in self._allowed_networks)

    def _check_rate_limit(self, source_ip: str) -> bool:
        """Check global and per-source rate limits.

        Returns True if the message should be accepted.
        Uses a simple sliding-window counter that resets each second.
        """
        now = time.monotonic()

        # --- Global rate limit ---
        if settings.SYSLOG_MAX_MESSAGES_PER_SECOND > 0:
            if now - self._global_window_start >= 1.0:
                self._global_msg_count = 0
                self._global_window_start = now

            if self._global_msg_count >= settings.SYSLOG_MAX_MESSAGES_PER_SECOND:
                return False
            self._global_msg_count += 1

        # --- Per-source rate limit ---
        if settings.SYSLOG_MAX_PER_SOURCE_PER_SECOND > 0:
            window_start = self._per_source_window_start[source_ip]
            if now - window_start >= 1.0:
                self._per_source_counts[source_ip] = 0
                self._per_source_window_start[source_ip] = now

            if self._per_source_counts[source_ip] >= settings.SYSLOG_MAX_PER_SOURCE_PER_SECOND:
                return False
            self._per_source_counts[source_ip] += 1

        return True

    def _parse_redaction_patterns(self) -> None:
        """Parse SYSLOG_REDACTION_PATTERNS into compiled regexes (SEC-023)."""
        raw = settings.SYSLOG_REDACTION_PATTERNS.strip()
        if not raw:
            return

        for pattern_str in raw.split(","):
            pattern_str = pattern_str.strip()
            if not pattern_str:
                continue
            try:
                self._redaction_patterns.append(re.compile(pattern_str))
            except re.error:
                logger.warning(
                    "invalid_redaction_pattern",
                    pattern=pattern_str,
                    reason="Could not compile as regex — skipping.",
                )

    def _redact_payload(self, text: str) -> str:
        """Apply redaction patterns to sensitive content (SEC-023).

        Replaces matched sensitive values with [REDACTED].
        """
        for pattern in self._redaction_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text

    def _truncate_payload(self, text: str) -> str:
        """Truncate payload to maximum stored size (SEC-023).

        Appends [TRUNCATED] marker if content exceeds limit.
        """
        max_size = settings.SYSLOG_MAX_STORED_PAYLOAD
        if max_size > 0 and len(text) > max_size:
            return text[:max_size] + " [TRUNCATED]"
        return text

    async def start(self) -> None:
        """Start the syslog collector."""
        logger.info(
            "Starting syslog collector",
            udp_port=settings.SYSLOG_UDP_PORT,
            max_message_size=settings.SYSLOG_MAX_MESSAGE_SIZE,
            global_rate_limit=settings.SYSLOG_MAX_MESSAGES_PER_SECOND,
            per_source_rate_limit=settings.SYSLOG_MAX_PER_SOURCE_PER_SECOND,
            ip_allowlist_enabled=self._ip_allowlist_enabled,
            allowed_networks_count=len(self._allowed_networks),
            max_buffer_size=settings.SYSLOG_MAX_BUFFER_SIZE,
            max_stored_payload=settings.SYSLOG_MAX_STORED_PAYLOAD,
            redaction_patterns_count=len(self._redaction_patterns),
        )

        # Connect to database
        self.db_pool = await asyncpg.create_pool(
            dsn=settings.POSTGRES_URL,
            min_size=5,
            max_size=20,
        )
        logger.info("Connected to PostgreSQL")

        # Connect to NATS
        self.nats = NATSClient()
        await self.nats.connect(servers=[settings.NATS_URL])
        logger.info("Connected to NATS")

        # Start UDP server
        loop = asyncio.get_event_loop()
        self.udp_transport, _ = await loop.create_datagram_endpoint(
            lambda: SyslogUDPProtocol(self),
            local_addr=("0.0.0.0", settings.SYSLOG_UDP_PORT),
        )
        logger.info("UDP listener started", port=settings.SYSLOG_UDP_PORT)

        self.running = True

        # Start background tasks
        asyncio.create_task(self.flush_buffer_periodically())
        asyncio.create_task(self.check_buffer_size_periodically())
        asyncio.create_task(self._report_drop_metrics_periodically())

    async def stop(self) -> None:
        """Stop the syslog collector."""
        logger.info("Stopping syslog collector")
        self.running = False

        # Flush remaining events
        await self.flush_buffer()

        if self.udp_transport:
            self.udp_transport.close()

        if self.nats:
            await self.nats.close()

        if self.db_pool:
            await self.db_pool.close()

        logger.info("Syslog collector stopped")

    async def process_message(self, data: bytes, addr: tuple[str, int]) -> None:
        """Process an incoming syslog message.

        Security checks applied in order:
        1. Message size cap
        2. IP allowlist
        3. Rate limiting (global + per-source)
        4. Backpressure (buffer fullness)
        """
        source_ip = addr[0]

        try:
            # --- SEC-015: Size cap ---
            if len(data) > settings.SYSLOG_MAX_MESSAGE_SIZE:
                self._drops_oversized += 1
                return

            # --- SEC-015: IP allowlist ---
            if not self._is_source_allowed(source_ip):
                self._drops_ip_denied += 1
                return

            # --- SEC-015: Rate limiting ---
            if not self._check_rate_limit(source_ip):
                self._drops_rate_limited += 1
                return

            # --- SEC-015: Backpressure ---
            if len(self.event_buffer) >= settings.SYSLOG_MAX_BUFFER_SIZE:
                self._drops_backpressure += 1
                return

            raw_message = data.decode("utf-8", errors="replace").strip()

            # Parse the message
            parsed = parse_syslog_message(raw_message)

            # --- SEC-023: Redact sensitive content before storage ---
            stored_message = self._redact_payload(parsed.message)
            stored_raw = self._redact_payload(raw_message)
            # Truncate to max stored payload size
            stored_raw = self._truncate_payload(stored_raw)

            # Create event record
            event = {
                "id": str(uuid4()),
                "source_ip": source_ip,
                "received_at": datetime.utcnow(),
                "facility": parsed.facility,
                "severity": parsed.severity,
                "version": parsed.version,
                "timestamp": parsed.timestamp,
                "hostname": parsed.hostname,
                "app_name": parsed.app_name,
                "proc_id": parsed.proc_id,
                "msg_id": parsed.msg_id,
                "structured_data": parsed.structured_data,
                "message": stored_message,
                "device_type": parsed.device_type,
                "event_type": parsed.event_type,
                "raw_message": stored_raw,
            }

            # Add to buffer
            async with self.buffer_lock:
                # Re-check buffer size under lock to prevent race
                if len(self.event_buffer) >= settings.SYSLOG_MAX_BUFFER_SIZE:
                    self._drops_backpressure += 1
                    return
                self.event_buffer.append(event)
                if len(self.event_buffer) >= self.batch_size:
                    await self._flush_buffer_internal()

            self._total_accepted += 1

            # Publish to NATS for real-time streaming
            await self._publish_to_nats(event, parsed)

        except Exception as e:
            logger.error("Failed to process syslog message", error=str(e), source_ip=source_ip)

    async def _publish_to_nats(self, event: dict[str, Any], parsed: ParsedSyslogMessage) -> None:
        """Publish event to NATS for real-time streaming."""
        if not self.nats:
            return

        try:
            # Prepare NATS message (convert datetime to ISO string)
            nats_event = {
                **event,
                "received_at": event["received_at"].isoformat(),
                "timestamp": event["timestamp"].isoformat() if event["timestamp"] else None,
            }

            # Publish to general syslog subject
            await self.nats.publish(
                "syslog.events",
                json.dumps(nats_event).encode(),
            )

            # Publish to severity-specific subject for alerts
            if parsed.severity <= 3:  # Critical and above
                await self.nats.publish(
                    f"syslog.alerts.{parsed.severity}",
                    json.dumps(nats_event).encode(),
                )

        except Exception as e:
            logger.error("Failed to publish to NATS", error=str(e))

    async def flush_buffer(self) -> None:
        """Flush the event buffer to the database."""
        async with self.buffer_lock:
            await self._flush_buffer_internal()

    async def _flush_buffer_internal(self) -> None:
        """Internal flush method (must be called with lock held)."""
        if not self.event_buffer or not self.db_pool:
            return

        events = self.event_buffer
        self.event_buffer = []

        try:
            # First, look up or create source records
            source_ids = await self._get_or_create_sources(events)

            # Batch insert events
            async with self.db_pool.acquire() as conn:
                await conn.executemany(
                    """
                    INSERT INTO syslog.events (
                        id, source_id, source_ip, received_at, facility, severity,
                        version, timestamp, hostname, app_name, proc_id, msg_id,
                        structured_data, message, device_type, event_type, raw_message
                    ) VALUES (
                        $1::uuid, $2::uuid, $3::inet, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13::jsonb, $14, $15, $16, $17
                    )
                    """,
                    [
                        (
                            e["id"],
                            source_ids.get(e["source_ip"]),
                            e["source_ip"],
                            e["received_at"],
                            e["facility"],
                            e["severity"],
                            e["version"],
                            e["timestamp"],
                            e["hostname"],
                            e["app_name"],
                            e["proc_id"],
                            e["msg_id"],
                            json.dumps(e["structured_data"]) if e["structured_data"] else None,
                            e["message"],
                            e["device_type"],
                            e["event_type"],
                            e["raw_message"],
                        )
                        for e in events
                    ],
                )

                # Update source statistics
                for source_ip, source_id in source_ids.items():
                    if source_id:
                        count = sum(1 for e in events if e["source_ip"] == source_ip)
                        await conn.execute(
                            """
                            UPDATE syslog.sources
                            SET events_received = events_received + $1,
                                last_event_at = NOW()
                            WHERE id = $2
                            """,
                            count,
                            source_id,
                        )

            logger.debug("Flushed events to database", count=len(events))

        except Exception as e:
            logger.error("Failed to flush events to database", error=str(e))
            # Re-add events to buffer on failure (with limit)
            if len(self.event_buffer) < self.batch_size * 10:
                self.event_buffer = events + self.event_buffer

    async def _get_or_create_sources(
        self, events: list[dict[str, Any]]
    ) -> dict[str, str | None]:
        """Get or create source records for events."""
        source_ids: dict[str, str | None] = {}

        if not self.db_pool:
            return source_ids

        # Get unique source IPs
        source_ips = set(e["source_ip"] for e in events)

        async with self.db_pool.acquire() as conn:
            for source_ip in source_ips:
                # Try to find existing source
                row = await conn.fetchrow(
                    "SELECT id FROM syslog.sources WHERE ip_address = $1::inet",
                    source_ip,
                )

                if row:
                    source_ids[source_ip] = str(row["id"])
                else:
                    # Auto-create source from first event with this IP
                    event = next(e for e in events if e["source_ip"] == source_ip)
                    hostname = event.get("hostname") or source_ip
                    device_type = event.get("device_type")

                    try:
                        result = await conn.fetchrow(
                            """
                            INSERT INTO syslog.sources (name, ip_address, hostname, device_type)
                            VALUES ($1, $2::inet, $3, $4)
                            ON CONFLICT (ip_address) DO UPDATE SET updated_at = NOW()
                            RETURNING id
                            """,
                            hostname,
                            source_ip,
                            hostname,
                            device_type,
                        )
                        source_ids[source_ip] = str(result["id"])
                    except Exception:
                        source_ids[source_ip] = None

        return source_ids

    async def flush_buffer_periodically(self) -> None:
        """Periodically flush the event buffer."""
        while self.running:
            await asyncio.sleep(5)  # Flush every 5 seconds
            await self.flush_buffer()

    async def check_buffer_size_periodically(self) -> None:
        """Periodically check and manage the 10GB circular buffer."""
        while self.running:
            await asyncio.sleep(self.buffer_check_interval)
            await self._manage_buffer_size()

    async def _report_drop_metrics_periodically(self) -> None:
        """Log drop metrics every 60 seconds for observability."""
        while self.running:
            await asyncio.sleep(60)
            if (
                self._drops_oversized
                or self._drops_rate_limited
                or self._drops_ip_denied
                or self._drops_backpressure
            ):
                logger.warning(
                    "syslog_collector_drop_metrics",
                    accepted=self._total_accepted,
                    drops_oversized=self._drops_oversized,
                    drops_rate_limited=self._drops_rate_limited,
                    drops_ip_denied=self._drops_ip_denied,
                    drops_backpressure=self._drops_backpressure,
                    buffer_size=len(self.event_buffer),
                )
            else:
                logger.debug(
                    "syslog_collector_metrics",
                    accepted=self._total_accepted,
                    buffer_size=len(self.event_buffer),
                )
            # Reset counters for next window
            self._drops_oversized = 0
            self._drops_rate_limited = 0
            self._drops_ip_denied = 0
            self._drops_backpressure = 0
            self._total_accepted = 0

    async def _manage_buffer_size(self) -> None:
        """
        Manage the circular buffer size.

        When buffer exceeds threshold, delete oldest events to make room.
        """
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Get current buffer settings
                settings_row = await conn.fetchrow(
                    """
                    SELECT max_size_bytes, cleanup_threshold_percent, retention_days
                    FROM syslog.buffer_settings
                    WHERE id = 1
                    """
                )

                if not settings_row:
                    return

                max_size_bytes = settings_row["max_size_bytes"]
                threshold_pct = settings_row["cleanup_threshold_percent"]
                retention_days = settings_row["retention_days"]

                # Calculate current size
                size_row = await conn.fetchrow(
                    """
                    SELECT pg_total_relation_size('syslog.events') as size
                    """
                )
                current_size = size_row["size"] if size_row else 0

                # Update current size in settings
                await conn.execute(
                    """
                    UPDATE syslog.buffer_settings
                    SET current_size_bytes = $1, updated_at = NOW()
                    WHERE id = 1
                    """,
                    current_size,
                )

                threshold_bytes = max_size_bytes * threshold_pct / 100

                if current_size > threshold_bytes:
                    logger.warning(
                        "Buffer threshold exceeded, cleaning up",
                        current_size_gb=current_size / 1073741824,
                        threshold_gb=threshold_bytes / 1073741824,
                    )

                    # Delete oldest events (10% of max size worth)
                    # First by retention, then by oldest
                    deleted = await conn.execute(
                        """
                        DELETE FROM syslog.events
                        WHERE received_at < NOW() - INTERVAL '%s days'
                        OR id IN (
                            SELECT id FROM syslog.events
                            ORDER BY received_at ASC
                            LIMIT 100000
                        )
                        """,
                        retention_days,
                    )

                    # Update cleanup timestamp
                    await conn.execute(
                        """
                        UPDATE syslog.buffer_settings
                        SET last_cleanup_at = NOW()
                        WHERE id = 1
                        """
                    )

                    logger.info(
                        "Buffer cleanup completed",
                        deleted_count=deleted.split()[-1] if deleted else 0,
                    )

        except Exception as e:
            logger.error("Failed to manage buffer size", error=str(e))


class SyslogUDPProtocol(asyncio.DatagramProtocol):
    """Asyncio UDP protocol for syslog reception.

    Performs a fast synchronous size check before spawning an async task
    to avoid unnecessary coroutine overhead for oversized packets.
    """

    def __init__(self, collector: SyslogCollector) -> None:
        self.collector = collector

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming UDP datagram.

        Fast-path rejection for oversized messages avoids async task creation.
        """
        if len(data) > settings.SYSLOG_MAX_MESSAGE_SIZE:
            self.collector._drops_oversized += 1
            return
        asyncio.create_task(self.collector.process_message(data, addr))

    def error_received(self, exc: Exception) -> None:
        """Handle UDP errors."""
        logger.error("UDP error received", error=str(exc))


async def main() -> None:
    """Main entry point for the syslog collector."""
    collector = SyslogCollector()

    # Set up signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(collector)))

    try:
        await collector.start()
        # Keep running
        while collector.running:
            await asyncio.sleep(1)
    finally:
        await collector.stop()


async def shutdown(collector: SyslogCollector) -> None:
    """Shutdown handler."""
    logger.info("Shutdown signal received")
    collector.running = False


if __name__ == "__main__":
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Collector terminated by user")
        sys.exit(0)

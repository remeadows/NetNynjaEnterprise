"""Network scanning service."""

import asyncio
import socket
from datetime import datetime, timezone
from typing import AsyncIterator

from netaddr import IPNetwork

from ..db import get_db, NetworkRepository, AddressRepository, ScanRepository
from ..models.network import Network
from ..models.address import IPAddressCreate, IPStatus, IPAddressDiscovered
from ..models.scan import ScanJob, ScanJobCreate, ScanType, ScanStatus, ScanProgress, ScanResult
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


async def ping_host(ip: str, timeout: float = 1.0) -> tuple[str, bool, float | None]:
    """
    Ping a host and return (ip, is_alive, response_time_ms).

    Uses TCP connect to port 7 (echo) as a fallback for ICMP.
    """
    try:
        start = asyncio.get_event_loop().time()

        # Try TCP connect as a ping alternative (works without root)
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, 7),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()

        elapsed = (asyncio.get_event_loop().time() - start) * 1000
        return ip, True, elapsed

    except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
        # Connection refused means host is alive but port closed
        pass

    # Try common ports as fallback
    for port in [22, 80, 443, 3389]:
        try:
            start = asyncio.get_event_loop().time()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout / 2,
            )
            writer.close()
            await writer.wait_closed()
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            return ip, True, elapsed
        except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
            continue

    return ip, False, None


async def resolve_hostname(ip: str) -> str | None:
    """Resolve IP address to hostname via reverse DNS."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, socket.gethostbyaddr, ip
        )
        return result[0] if result else None
    except (socket.herror, socket.gaierror, OSError):
        return None


class ScannerService:
    """Service for network scanning operations."""

    def __init__(self) -> None:
        self.concurrency = settings.scan_concurrency
        self.ping_timeout = settings.ping_timeout

    async def start_scan(
        self, network_id: str, scan_type: ScanType = ScanType.PING
    ) -> ScanJob:
        """Start a new network scan."""
        async with get_db() as conn:
            network_repo = NetworkRepository(conn)
            scan_repo = ScanRepository(conn)

            network = await network_repo.find_by_id(network_id)
            if not network:
                raise ValueError(f"Network {network_id} not found")

            # Create scan job
            job = await scan_repo.create(
                ScanJobCreate(network_id=network_id, scan_type=scan_type)
            )

            logger.info(
                "scan_started",
                scan_id=job.id,
                network_id=network_id,
                network=network.network,
                scan_type=scan_type.value,
            )

            return job

    async def run_scan(self, scan_id: str) -> ScanResult:
        """Execute a scan job."""
        async with get_db() as conn:
            scan_repo = ScanRepository(conn)
            network_repo = NetworkRepository(conn)
            address_repo = AddressRepository(conn)

            scan = await scan_repo.find_by_id(scan_id)
            if not scan:
                raise ValueError(f"Scan {scan_id} not found")

            network = await network_repo.find_by_id(scan.network_id)
            if not network:
                raise ValueError(f"Network {scan.network_id} not found")

            # Update status to running
            await scan_repo.update_status(scan_id, ScanStatus.RUNNING)

            start_time = datetime.now(timezone.utc)
            active_ips: set[str] = set()
            new_ips = 0
            total_ips = 0

            try:
                # Generate IP range from CIDR
                ip_network = IPNetwork(network.network)
                all_ips = [str(ip) for ip in ip_network.iter_hosts()]
                total_ips = len(all_ips)

                logger.info(
                    "scanning_network",
                    scan_id=scan_id,
                    network=network.network,
                    total_ips=total_ips,
                )

                # Scan in batches
                async for discovered in self._scan_batch(all_ips):
                    if discovered.is_alive:
                        active_ips.add(discovered.address)

                        # Check if this is a new IP
                        existing = await address_repo.find_by_ip(
                            network.id, discovered.address
                        )
                        if not existing:
                            new_ips += 1

                        # Upsert the discovered address
                        await address_repo.upsert(
                            IPAddressCreate(
                                network_id=network.id,
                                address=discovered.address,
                                hostname=discovered.hostname,
                                mac_address=discovered.mac_address,
                                status=IPStatus.ACTIVE,
                            )
                        )

                # Mark addresses not seen as inactive
                disappeared = await address_repo.mark_inactive(network.id, active_ips)

                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds()

                # Update scan with results
                await scan_repo.update_status(
                    scan_id,
                    ScanStatus.COMPLETED,
                    total_ips=total_ips,
                    active_ips=len(active_ips),
                    new_ips=new_ips,
                )

                logger.info(
                    "scan_completed",
                    scan_id=scan_id,
                    duration_seconds=duration,
                    total_ips=total_ips,
                    active_ips=len(active_ips),
                    new_ips=new_ips,
                    disappeared_ips=disappeared,
                )

                return ScanResult(
                    scan_id=scan_id,
                    network_id=network.id,
                    scan_type=scan.scan_type,
                    status=ScanStatus.COMPLETED,
                    started_at=start_time,
                    completed_at=end_time,
                    duration_seconds=duration,
                    total_ips=total_ips,
                    active_ips=len(active_ips),
                    new_ips=new_ips,
                    updated_ips=len(active_ips) - new_ips,
                    disappeared_ips=disappeared,
                )

            except Exception as e:
                error_msg = str(e)
                logger.error("scan_failed", scan_id=scan_id, error=error_msg)

                await scan_repo.update_status(
                    scan_id,
                    ScanStatus.FAILED,
                    error_message=error_msg,
                )

                end_time = datetime.now(timezone.utc)
                return ScanResult(
                    scan_id=scan_id,
                    network_id=network.id,
                    scan_type=scan.scan_type,
                    status=ScanStatus.FAILED,
                    started_at=start_time,
                    completed_at=end_time,
                    duration_seconds=(end_time - start_time).total_seconds(),
                    total_ips=total_ips,
                    active_ips=len(active_ips),
                    new_ips=new_ips,
                    updated_ips=0,
                    disappeared_ips=0,
                    error_message=error_msg,
                )

    async def _scan_batch(
        self, ips: list[str]
    ) -> AsyncIterator[IPAddressDiscovered]:
        """Scan IPs in concurrent batches."""
        semaphore = asyncio.Semaphore(self.concurrency)

        async def scan_with_limit(ip: str) -> IPAddressDiscovered | None:
            async with semaphore:
                ip_addr, is_alive, response_time = await ping_host(ip, self.ping_timeout)
                if is_alive:
                    hostname = await resolve_hostname(ip)
                    return IPAddressDiscovered(
                        address=ip_addr,
                        hostname=hostname,
                        response_time_ms=response_time,
                        is_alive=True,
                    )
                return IPAddressDiscovered(address=ip_addr, is_alive=False)

        # Process all IPs concurrently (respecting semaphore limit)
        tasks = [scan_with_limit(ip) for ip in ips]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                yield result

    async def get_scan_status(self, scan_id: str) -> ScanJob | None:
        """Get current status of a scan job."""
        async with get_db() as conn:
            scan_repo = ScanRepository(conn)
            return await scan_repo.find_by_id(scan_id)

    async def get_network_scans(
        self, network_id: str, limit: int = 10
    ) -> list[ScanJob]:
        """Get recent scans for a network."""
        async with get_db() as conn:
            scan_repo = ScanRepository(conn)
            return await scan_repo.find_by_network(network_id, limit)

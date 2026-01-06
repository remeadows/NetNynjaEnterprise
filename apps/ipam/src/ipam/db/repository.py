"""Database repositories for IPAM entities."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from asyncpg import Connection

from ..models.network import Network, NetworkCreate, NetworkUpdate, NetworkWithStats
from ..models.address import IPAddress, IPAddressCreate, IPAddressUpdate, IPStatus
from ..models.scan import ScanJob, ScanJobCreate, ScanStatus, ScanType
from ..models.common import NetworkStats
from ..core.logging import get_logger

logger = get_logger(__name__)


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Convert asyncpg Record to dictionary."""
    return dict(row) if row else {}


class NetworkRepository:
    """Repository for network/subnet operations."""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    async def find_all(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Network], int]:
        """Find all networks with pagination and optional filters."""
        where_clauses = []
        params: list[Any] = []
        param_idx = 1

        if search:
            where_clauses.append(
                f"(name ILIKE ${param_idx} OR network::text ILIKE ${param_idx} OR location ILIKE ${param_idx})"
            )
            params.append(f"%{search}%")
            param_idx += 1

        if is_active is not None:
            where_clauses.append(f"is_active = ${param_idx}")
            params.append(is_active)
            param_idx += 1

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM ipam.networks {where_sql}"
        total = await self.conn.fetchval(count_sql, *params)

        # Get paginated results
        offset = (page - 1) * limit
        params.extend([limit, offset])

        query = f"""
            SELECT id, name, network::text, vlan_id, description, location,
                   gateway::text, dns_servers::text[] as dns_servers, is_active,
                   created_by, created_at, updated_at
            FROM ipam.networks
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """

        rows = await self.conn.fetch(query, *params)
        networks = [Network(**_row_to_dict(row)) for row in rows]

        return networks, total

    async def find_by_id(self, network_id: str) -> Network | None:
        """Find a network by ID."""
        query = """
            SELECT id, name, network::text, vlan_id, description, location,
                   gateway::text, dns_servers::text[] as dns_servers, is_active,
                   created_by, created_at, updated_at
            FROM ipam.networks
            WHERE id = $1
        """
        row = await self.conn.fetchrow(query, UUID(network_id))
        return Network(**_row_to_dict(row)) if row else None

    async def find_by_cidr(self, cidr: str) -> Network | None:
        """Find a network by CIDR."""
        query = """
            SELECT id, name, network::text, vlan_id, description, location,
                   gateway::text, dns_servers::text[] as dns_servers, is_active,
                   created_by, created_at, updated_at
            FROM ipam.networks
            WHERE network = $1::cidr
        """
        row = await self.conn.fetchrow(query, cidr)
        return Network(**_row_to_dict(row)) if row else None

    async def create(self, data: NetworkCreate, created_by: str | None = None) -> Network:
        """Create a new network."""
        query = """
            INSERT INTO ipam.networks (
                name, network, vlan_id, description, location,
                gateway, dns_servers, is_active, created_by
            )
            VALUES ($1, $2::cidr, $3, $4, $5, $6::inet, $7::inet[], $8, $9)
            RETURNING id, name, network::text, vlan_id, description, location,
                      gateway::text, dns_servers::text[] as dns_servers, is_active,
                      created_by, created_at, updated_at
        """
        row = await self.conn.fetchrow(
            query,
            data.name,
            data.network,
            data.vlan_id,
            data.description,
            data.location,
            data.gateway,
            data.dns_servers,
            data.is_active,
            UUID(created_by) if created_by else None,
        )
        logger.info("network_created", network_id=str(row["id"]), name=data.name)
        return Network(**_row_to_dict(row))

    async def update(self, network_id: str, data: NetworkUpdate) -> Network | None:
        """Update an existing network."""
        # Build dynamic update query
        updates = []
        params: list[Any] = [UUID(network_id)]
        param_idx = 2

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "network":
                updates.append(f"network = ${param_idx}::cidr")
            elif field == "gateway":
                updates.append(f"gateway = ${param_idx}::inet")
            elif field == "dns_servers":
                updates.append(f"dns_servers = ${param_idx}::inet[]")
            else:
                updates.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1

        if not updates:
            return await self.find_by_id(network_id)

        query = f"""
            UPDATE ipam.networks
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = $1
            RETURNING id, name, network::text, vlan_id, description, location,
                      gateway::text, dns_servers::text[] as dns_servers, is_active,
                      created_by, created_at, updated_at
        """
        row = await self.conn.fetchrow(query, *params)
        if row:
            logger.info("network_updated", network_id=network_id)
        return Network(**_row_to_dict(row)) if row else None

    async def delete(self, network_id: str) -> bool:
        """Delete a network by ID."""
        query = "DELETE FROM ipam.networks WHERE id = $1"
        result = await self.conn.execute(query, UUID(network_id))
        deleted = result == "DELETE 1"
        if deleted:
            logger.info("network_deleted", network_id=network_id)
        return deleted

    async def get_stats(self, network_id: str) -> NetworkStats | None:
        """Get statistics for a network."""
        query = """
            WITH addr_stats AS (
                SELECT
                    network_id,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'inactive') as inactive,
                    COUNT(*) FILTER (WHERE status = 'reserved') as reserved,
                    COUNT(*) FILTER (WHERE status = 'dhcp') as dhcp,
                    COUNT(*) FILTER (WHERE status = 'unknown') as unknown
                FROM ipam.addresses
                WHERE network_id = $1
                GROUP BY network_id
            ),
            last_scan AS (
                SELECT started_at
                FROM ipam.scan_history
                WHERE network_id = $1 AND status = 'completed'
                ORDER BY started_at DESC
                LIMIT 1
            ),
            network_size AS (
                SELECT
                    (host(broadcast(network)) - host(network(network)))::int - 1 as total_addresses
                FROM ipam.networks
                WHERE id = $1
            )
            SELECT
                $1 as network_id,
                COALESCE(ns.total_addresses, 0) as total_addresses,
                COALESCE(a.total, 0) as used_addresses,
                COALESCE(ns.total_addresses, 0) - COALESCE(a.total, 0) as available_addresses,
                CASE
                    WHEN ns.total_addresses > 0 THEN
                        ROUND((COALESCE(a.total, 0)::float / ns.total_addresses * 100)::numeric, 2)
                    ELSE 0
                END as utilization_percent,
                COALESCE(a.active, 0) as active_count,
                COALESCE(a.inactive, 0) as inactive_count,
                COALESCE(a.reserved, 0) as reserved_count,
                COALESCE(a.dhcp, 0) as dhcp_count,
                COALESCE(a.unknown, 0) as unknown_count,
                ls.started_at as last_scan
            FROM network_size ns
            LEFT JOIN addr_stats a ON true
            LEFT JOIN last_scan ls ON true
        """
        row = await self.conn.fetchrow(query, UUID(network_id))
        return NetworkStats(**_row_to_dict(row)) if row else None


class AddressRepository:
    """Repository for IP address operations."""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    async def find_by_network(
        self,
        network_id: str,
        page: int = 1,
        limit: int = 50,
        status: IPStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[IPAddress], int]:
        """Find all IP addresses in a network with pagination."""
        where_clauses = ["network_id = $1"]
        params: list[Any] = [UUID(network_id)]
        param_idx = 2

        if status:
            where_clauses.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        if search:
            where_clauses.append(
                f"(address::text ILIKE ${param_idx} OR hostname ILIKE ${param_idx} OR mac_address::text ILIKE ${param_idx})"
            )
            params.append(f"%{search}%")
            param_idx += 1

        where_sql = f"WHERE {' AND '.join(where_clauses)}"

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM ipam.addresses {where_sql}"
        total = await self.conn.fetchval(count_sql, *params)

        # Get paginated results
        offset = (page - 1) * limit
        params.extend([limit, offset])

        query = f"""
            SELECT id, network_id, address::text, mac_address::text, hostname, fqdn,
                   status, device_type, description, last_seen, discovered_at,
                   created_at, updated_at
            FROM ipam.addresses
            {where_sql}
            ORDER BY address
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """

        rows = await self.conn.fetch(query, *params)
        addresses = [IPAddress(**_row_to_dict(row)) for row in rows]

        return addresses, total

    async def find_by_id(self, address_id: str) -> IPAddress | None:
        """Find an IP address by ID."""
        query = """
            SELECT id, network_id, address::text, mac_address::text, hostname, fqdn,
                   status, device_type, description, last_seen, discovered_at,
                   created_at, updated_at
            FROM ipam.addresses
            WHERE id = $1
        """
        row = await self.conn.fetchrow(query, UUID(address_id))
        return IPAddress(**_row_to_dict(row)) if row else None

    async def find_by_ip(self, network_id: str, address: str) -> IPAddress | None:
        """Find an IP address by network and IP."""
        query = """
            SELECT id, network_id, address::text, mac_address::text, hostname, fqdn,
                   status, device_type, description, last_seen, discovered_at,
                   created_at, updated_at
            FROM ipam.addresses
            WHERE network_id = $1 AND address = $2::inet
        """
        row = await self.conn.fetchrow(query, UUID(network_id), address)
        return IPAddress(**_row_to_dict(row)) if row else None

    async def create(self, data: IPAddressCreate) -> IPAddress:
        """Create a new IP address record."""
        query = """
            INSERT INTO ipam.addresses (
                network_id, address, mac_address, hostname, fqdn,
                status, device_type, description, discovered_at
            )
            VALUES ($1, $2::inet, $3::macaddr, $4, $5, $6, $7, $8, NOW())
            RETURNING id, network_id, address::text, mac_address::text, hostname, fqdn,
                      status, device_type, description, last_seen, discovered_at,
                      created_at, updated_at
        """
        row = await self.conn.fetchrow(
            query,
            UUID(data.network_id),
            data.address,
            data.mac_address,
            data.hostname,
            data.fqdn,
            data.status.value,
            data.device_type,
            data.description,
        )
        return IPAddress(**_row_to_dict(row))

    async def upsert(self, data: IPAddressCreate) -> IPAddress:
        """Create or update an IP address (for scan results)."""
        query = """
            INSERT INTO ipam.addresses (
                network_id, address, mac_address, hostname, fqdn,
                status, device_type, description, last_seen, discovered_at
            )
            VALUES ($1, $2::inet, $3::macaddr, $4, $5, $6, $7, $8, NOW(),
                    COALESCE((SELECT discovered_at FROM ipam.addresses WHERE network_id = $1 AND address = $2::inet), NOW()))
            ON CONFLICT (network_id, address)
            DO UPDATE SET
                mac_address = COALESCE(EXCLUDED.mac_address, ipam.addresses.mac_address),
                hostname = COALESCE(EXCLUDED.hostname, ipam.addresses.hostname),
                status = EXCLUDED.status,
                last_seen = NOW(),
                updated_at = NOW()
            RETURNING id, network_id, address::text, mac_address::text, hostname, fqdn,
                      status, device_type, description, last_seen, discovered_at,
                      created_at, updated_at
        """
        row = await self.conn.fetchrow(
            query,
            UUID(data.network_id),
            data.address,
            data.mac_address,
            data.hostname,
            data.fqdn,
            data.status.value,
            data.device_type,
            data.description,
        )
        return IPAddress(**_row_to_dict(row))

    async def update(self, address_id: str, data: IPAddressUpdate) -> IPAddress | None:
        """Update an existing IP address."""
        updates = []
        params: list[Any] = [UUID(address_id)]
        param_idx = 2

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "mac_address":
                updates.append(f"mac_address = ${param_idx}::macaddr")
            elif field == "status":
                updates.append(f"status = ${param_idx}")
                value = value.value if hasattr(value, "value") else value
            else:
                updates.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1

        if not updates:
            return await self.find_by_id(address_id)

        query = f"""
            UPDATE ipam.addresses
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = $1
            RETURNING id, network_id, address::text, mac_address::text, hostname, fqdn,
                      status, device_type, description, last_seen, discovered_at,
                      created_at, updated_at
        """
        row = await self.conn.fetchrow(query, *params)
        return IPAddress(**_row_to_dict(row)) if row else None

    async def delete(self, address_id: str) -> bool:
        """Delete an IP address by ID."""
        query = "DELETE FROM ipam.addresses WHERE id = $1"
        result = await self.conn.execute(query, UUID(address_id))
        return result == "DELETE 1"

    async def mark_inactive(self, network_id: str, active_ips: set[str]) -> int:
        """Mark addresses not in the active set as inactive."""
        if not active_ips:
            return 0

        query = """
            UPDATE ipam.addresses
            SET status = 'inactive', updated_at = NOW()
            WHERE network_id = $1
              AND address::text != ALL($2)
              AND status = 'active'
        """
        result = await self.conn.execute(query, UUID(network_id), list(active_ips))
        # Parse "UPDATE N" to get count
        return int(result.split()[1]) if result.startswith("UPDATE") else 0


class ScanRepository:
    """Repository for scan job operations."""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    async def create(self, data: ScanJobCreate) -> ScanJob:
        """Create a new scan job."""
        query = """
            INSERT INTO ipam.scan_history (network_id, scan_type, started_at, status)
            VALUES ($1, $2, NOW(), 'pending')
            RETURNING id, network_id, scan_type, status, started_at, completed_at,
                      total_ips, active_ips, new_ips, error_message
        """
        row = await self.conn.fetchrow(
            query, UUID(data.network_id), data.scan_type.value
        )
        logger.info("scan_job_created", scan_id=str(row["id"]), network_id=data.network_id)
        return ScanJob(**_row_to_dict(row))

    async def find_by_id(self, scan_id: str) -> ScanJob | None:
        """Find a scan job by ID."""
        query = """
            SELECT id, network_id, scan_type, status, started_at, completed_at,
                   total_ips, active_ips, new_ips, error_message
            FROM ipam.scan_history
            WHERE id = $1
        """
        row = await self.conn.fetchrow(query, UUID(scan_id))
        return ScanJob(**_row_to_dict(row)) if row else None

    async def find_by_network(
        self, network_id: str, limit: int = 10
    ) -> list[ScanJob]:
        """Find recent scan jobs for a network."""
        query = """
            SELECT id, network_id, scan_type, status, started_at, completed_at,
                   total_ips, active_ips, new_ips, error_message
            FROM ipam.scan_history
            WHERE network_id = $1
            ORDER BY started_at DESC
            LIMIT $2
        """
        rows = await self.conn.fetch(query, UUID(network_id), limit)
        return [ScanJob(**_row_to_dict(row)) for row in rows]

    async def update_status(
        self,
        scan_id: str,
        status: ScanStatus,
        total_ips: int | None = None,
        active_ips: int | None = None,
        new_ips: int | None = None,
        error_message: str | None = None,
    ) -> ScanJob | None:
        """Update scan job status and results."""
        updates = ["status = $2"]
        params: list[Any] = [UUID(scan_id), status.value]
        param_idx = 3

        if status in (ScanStatus.COMPLETED, ScanStatus.FAILED):
            updates.append("completed_at = NOW()")

        if total_ips is not None:
            updates.append(f"total_ips = ${param_idx}")
            params.append(total_ips)
            param_idx += 1

        if active_ips is not None:
            updates.append(f"active_ips = ${param_idx}")
            params.append(active_ips)
            param_idx += 1

        if new_ips is not None:
            updates.append(f"new_ips = ${param_idx}")
            params.append(new_ips)
            param_idx += 1

        if error_message is not None:
            updates.append(f"error_message = ${param_idx}")
            params.append(error_message)

        query = f"""
            UPDATE ipam.scan_history
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING id, network_id, scan_type, status, started_at, completed_at,
                      total_ips, active_ips, new_ips, error_message
        """
        row = await self.conn.fetchrow(query, *params)
        if row:
            logger.info("scan_status_updated", scan_id=scan_id, status=status.value)
        return ScanJob(**_row_to_dict(row)) if row else None

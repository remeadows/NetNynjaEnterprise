"""Network management service."""

from ..db import get_db, NetworkRepository, AddressRepository
from ..models.network import Network, NetworkCreate, NetworkUpdate, NetworkWithStats
from ..models.address import IPAddress, IPAddressCreate, IPAddressUpdate, IPStatus
from ..models.common import NetworkStats, PaginatedResponse, Pagination
from ..core.logging import get_logger

logger = get_logger(__name__)


class NetworkService:
    """Service for network management operations."""

    async def list_networks(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> PaginatedResponse[Network]:
        """List all networks with pagination and filters."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)
            networks, total = await repo.find_all(
                page=page, limit=limit, search=search, is_active=is_active
            )

            pages = (total + limit - 1) // limit if total > 0 else 0

            return PaginatedResponse(
                data=networks,
                pagination=Pagination(page=page, limit=limit, total=total, pages=pages),
            )

    async def get_network(self, network_id: str) -> Network | None:
        """Get a network by ID."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)
            return await repo.find_by_id(network_id)

    async def get_network_with_stats(self, network_id: str) -> NetworkWithStats | None:
        """Get a network with utilization statistics."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)
            network = await repo.find_by_id(network_id)
            if not network:
                return None

            stats = await repo.get_stats(network_id)
            return NetworkWithStats(
                **network.model_dump(),
                total_addresses=stats.total_addresses if stats else 0,
                used_addresses=stats.used_addresses if stats else 0,
                utilization_percent=stats.utilization_percent if stats else 0.0,
                last_scan=stats.last_scan if stats else None,
            )

    async def create_network(
        self, data: NetworkCreate, created_by: str | None = None
    ) -> Network:
        """Create a new network."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)

            # Check for duplicate CIDR
            existing = await repo.find_by_cidr(data.network)
            if existing:
                raise ValueError(f"Network {data.network} already exists")

            return await repo.create(data, created_by)

    async def update_network(
        self, network_id: str, data: NetworkUpdate
    ) -> Network | None:
        """Update an existing network."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)

            # Check if network exists
            existing = await repo.find_by_id(network_id)
            if not existing:
                return None

            # Check for duplicate CIDR if changing
            if data.network and data.network != existing.network:
                duplicate = await repo.find_by_cidr(data.network)
                if duplicate:
                    raise ValueError(f"Network {data.network} already exists")

            return await repo.update(network_id, data)

    async def delete_network(self, network_id: str) -> bool:
        """Delete a network and all associated addresses."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)
            return await repo.delete(network_id)

    async def get_network_stats(self, network_id: str) -> NetworkStats | None:
        """Get detailed statistics for a network."""
        async with get_db() as conn:
            repo = NetworkRepository(conn)
            return await repo.get_stats(network_id)

    async def list_addresses(
        self,
        network_id: str,
        page: int = 1,
        limit: int = 50,
        status: IPStatus | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[IPAddress]:
        """List IP addresses in a network."""
        async with get_db() as conn:
            repo = AddressRepository(conn)
            addresses, total = await repo.find_by_network(
                network_id=network_id,
                page=page,
                limit=limit,
                status=status,
                search=search,
            )

            pages = (total + limit - 1) // limit if total > 0 else 0

            return PaginatedResponse(
                data=addresses,
                pagination=Pagination(page=page, limit=limit, total=total, pages=pages),
            )

    async def get_address(self, address_id: str) -> IPAddress | None:
        """Get an IP address by ID."""
        async with get_db() as conn:
            repo = AddressRepository(conn)
            return await repo.find_by_id(address_id)

    async def create_address(self, data: IPAddressCreate) -> IPAddress:
        """Create a new IP address record."""
        async with get_db() as conn:
            repo = AddressRepository(conn)
            return await repo.create(data)

    async def update_address(
        self, address_id: str, data: IPAddressUpdate
    ) -> IPAddress | None:
        """Update an existing IP address."""
        async with get_db() as conn:
            repo = AddressRepository(conn)
            return await repo.update(address_id, data)

    async def delete_address(self, address_id: str) -> bool:
        """Delete an IP address."""
        async with get_db() as conn:
            repo = AddressRepository(conn)
            return await repo.delete(address_id)

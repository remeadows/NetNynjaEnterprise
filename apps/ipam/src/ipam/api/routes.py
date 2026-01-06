"""IPAM API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks

from ..core.auth import JWTPayload, get_current_user, require_operator, require_admin
from ..services.network import NetworkService
from ..services.scanner import ScannerService
from ..services.metrics import MetricsService
from ..models.network import Network, NetworkCreate, NetworkUpdate, NetworkWithStats
from ..models.address import IPAddress, IPAddressCreate, IPAddressUpdate, IPStatus
from ..models.scan import ScanJob, ScanType, ScanResult
from ..models.common import PaginatedResponse, APIResponse, NetworkStats

router = APIRouter(prefix="/api/v1/ipam", tags=["IPAM"])

# Service instances
network_service = NetworkService()
scanner_service = ScannerService()
metrics_service = MetricsService()


# Network endpoints
@router.get("/networks", response_model=PaginatedResponse[Network])
async def list_networks(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    is_active: bool | None = None,
    _user: JWTPayload = Depends(get_current_user),
) -> PaginatedResponse[Network]:
    """List all networks with pagination and optional filters."""
    return await network_service.list_networks(
        page=page, limit=limit, search=search, is_active=is_active
    )


@router.get("/networks/{network_id}", response_model=APIResponse[NetworkWithStats])
async def get_network(
    network_id: str,
    _user: JWTPayload = Depends(get_current_user),
) -> APIResponse[NetworkWithStats]:
    """Get a network by ID with utilization statistics."""
    network = await network_service.get_network_with_stats(network_id)
    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )
    return APIResponse(data=network)


@router.post("/networks", response_model=APIResponse[Network], status_code=status.HTTP_201_CREATED)
async def create_network(
    data: NetworkCreate,
    user: JWTPayload = Depends(require_operator),
) -> APIResponse[Network]:
    """Create a new network (requires operator role)."""
    try:
        network = await network_service.create_network(data, created_by=user.sub)
        return APIResponse(data=network, message="Network created successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/networks/{network_id}", response_model=APIResponse[Network])
async def update_network(
    network_id: str,
    data: NetworkUpdate,
    _user: JWTPayload = Depends(require_operator),
) -> APIResponse[Network]:
    """Update an existing network (requires operator role)."""
    try:
        network = await network_service.update_network(network_id, data)
        if not network:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Network {network_id} not found",
            )
        return APIResponse(data=network, message="Network updated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/networks/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_network(
    network_id: str,
    _user: JWTPayload = Depends(require_admin),
) -> None:
    """Delete a network (requires admin role)."""
    deleted = await network_service.delete_network(network_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )


@router.get("/networks/{network_id}/stats", response_model=APIResponse[NetworkStats])
async def get_network_stats(
    network_id: str,
    _user: JWTPayload = Depends(get_current_user),
) -> APIResponse[NetworkStats]:
    """Get detailed statistics for a network."""
    stats = await network_service.get_network_stats(network_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Network {network_id} not found",
        )
    return APIResponse(data=stats)


# IP Address endpoints
@router.get("/networks/{network_id}/addresses", response_model=PaginatedResponse[IPAddress])
async def list_addresses(
    network_id: str,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    status: IPStatus | None = None,
    search: str | None = None,
    _user: JWTPayload = Depends(get_current_user),
) -> PaginatedResponse[IPAddress]:
    """List IP addresses in a network."""
    return await network_service.list_addresses(
        network_id=network_id,
        page=page,
        limit=limit,
        status=status,
        search=search,
    )


@router.get("/addresses/{address_id}", response_model=APIResponse[IPAddress])
async def get_address(
    address_id: str,
    _user: JWTPayload = Depends(get_current_user),
) -> APIResponse[IPAddress]:
    """Get an IP address by ID."""
    address = await network_service.get_address(address_id)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found",
        )
    return APIResponse(data=address)


@router.post("/addresses", response_model=APIResponse[IPAddress], status_code=status.HTTP_201_CREATED)
async def create_address(
    data: IPAddressCreate,
    _user: JWTPayload = Depends(require_operator),
) -> APIResponse[IPAddress]:
    """Create a new IP address record (requires operator role)."""
    address = await network_service.create_address(data)
    return APIResponse(data=address, message="Address created successfully")


@router.put("/addresses/{address_id}", response_model=APIResponse[IPAddress])
async def update_address(
    address_id: str,
    data: IPAddressUpdate,
    _user: JWTPayload = Depends(require_operator),
) -> APIResponse[IPAddress]:
    """Update an existing IP address (requires operator role)."""
    address = await network_service.update_address(address_id, data)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found",
        )
    return APIResponse(data=address, message="Address updated successfully")


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str,
    _user: JWTPayload = Depends(require_admin),
) -> None:
    """Delete an IP address (requires admin role)."""
    deleted = await network_service.delete_address(address_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address {address_id} not found",
        )


# Scan endpoints
@router.post("/networks/{network_id}/scan", response_model=APIResponse[ScanJob])
async def start_scan(
    network_id: str,
    scan_type: ScanType = ScanType.PING,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    _user: JWTPayload = Depends(require_operator),
) -> APIResponse[ScanJob]:
    """Start a network scan (requires operator role)."""
    try:
        # Create the scan job
        scan_job = await scanner_service.start_scan(network_id, scan_type)

        # Run scan in background
        background_tasks.add_task(scanner_service.run_scan, scan_job.id)

        return APIResponse(data=scan_job, message="Scan started")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/scans/{scan_id}", response_model=APIResponse[ScanJob])
async def get_scan_status(
    scan_id: str,
    _user: JWTPayload = Depends(get_current_user),
) -> APIResponse[ScanJob]:
    """Get the status of a scan job."""
    scan = await scanner_service.get_scan_status(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )
    return APIResponse(data=scan)


@router.get("/networks/{network_id}/scans", response_model=APIResponse[list[ScanJob]])
async def list_network_scans(
    network_id: str,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    _user: JWTPayload = Depends(get_current_user),
) -> APIResponse[list[ScanJob]]:
    """Get recent scans for a network."""
    scans = await scanner_service.get_network_scans(network_id, limit)
    return APIResponse(data=scans)


# Dashboard endpoint
@router.get("/dashboard")
async def get_dashboard(
    _user: JWTPayload = Depends(get_current_user),
) -> APIResponse[dict]:
    """Get IPAM dashboard metrics."""
    metrics = await metrics_service.get_dashboard_metrics()
    return APIResponse(data=metrics)

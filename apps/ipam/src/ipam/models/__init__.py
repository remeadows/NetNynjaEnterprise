"""Pydantic models for IPAM entities."""

from .network import (
    Network,
    NetworkCreate,
    NetworkUpdate,
    NetworkWithStats,
)
from .address import (
    IPAddress,
    IPAddressCreate,
    IPAddressUpdate,
    IPAddressBulkCreate,
    IPStatus,
)
from .scan import (
    ScanJob,
    ScanJobCreate,
    ScanType,
    ScanStatus,
    ScanResult,
)
from .common import (
    PaginatedResponse,
    APIResponse,
    NetworkStats,
)

__all__ = [
    "Network",
    "NetworkCreate",
    "NetworkUpdate",
    "NetworkWithStats",
    "IPAddress",
    "IPAddressCreate",
    "IPAddressUpdate",
    "IPAddressBulkCreate",
    "IPStatus",
    "ScanJob",
    "ScanJobCreate",
    "ScanType",
    "ScanStatus",
    "ScanResult",
    "PaginatedResponse",
    "APIResponse",
    "NetworkStats",
]

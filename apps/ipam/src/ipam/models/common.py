"""Common models and response schemas."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    """Pagination metadata."""

    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    success: bool = True
    data: list[T]
    pagination: Pagination


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    error: str
    code: str | None = None
    details: dict[str, Any] | None = None


class NetworkStats(BaseModel):
    """Network utilization statistics."""

    network_id: str
    total_addresses: int
    used_addresses: int
    available_addresses: int
    utilization_percent: float = Field(ge=0, le=100)
    active_count: int = 0
    inactive_count: int = 0
    reserved_count: int = 0
    dhcp_count: int = 0
    unknown_count: int = 0
    last_scan: datetime | None = None


class DashboardStats(BaseModel):
    """IPAM dashboard statistics."""

    total_networks: int
    total_addresses: int
    active_addresses: int
    average_utilization: float
    networks_by_status: dict[str, int]
    recent_scans: int
    alerts: int

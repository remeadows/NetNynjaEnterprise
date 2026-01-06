"""Scan job models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ScanType(str, Enum):
    """Type of network scan."""

    PING = "ping"
    TCP = "tcp"
    ARP = "arp"
    NMAP = "nmap"


class ScanStatus(str, Enum):
    """Scan job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanJobCreate(BaseModel):
    """Scan job creation request."""

    network_id: str
    scan_type: ScanType = ScanType.PING
    ports: list[int] | None = None  # For TCP scans
    options: dict[str, Any] | None = None


class ScanJob(BaseModel):
    """Complete scan job entity."""

    id: str
    network_id: str
    scan_type: ScanType
    status: ScanStatus
    started_at: datetime
    completed_at: datetime | None = None
    total_ips: int = 0
    active_ips: int = 0
    new_ips: int = 0
    error_message: str | None = None
    options: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class ScanProgress(BaseModel):
    """Real-time scan progress update."""

    scan_id: str
    network_id: str
    status: ScanStatus
    progress_percent: float = Field(ge=0, le=100)
    scanned_count: int = 0
    total_count: int = 0
    active_found: int = 0
    current_ip: str | None = None
    elapsed_seconds: float = 0


class ScanResult(BaseModel):
    """Final scan result summary."""

    scan_id: str
    network_id: str
    scan_type: ScanType
    status: ScanStatus
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    total_ips: int
    active_ips: int
    new_ips: int
    updated_ips: int
    disappeared_ips: int
    error_message: str | None = None

"""IP Address models."""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class IPStatus(str, Enum):
    """IP address status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    RESERVED = "reserved"
    DHCP = "dhcp"
    UNKNOWN = "unknown"


class IPAddressBase(BaseModel):
    """Base IP address fields."""

    address: str
    hostname: str | None = None
    fqdn: str | None = None
    mac_address: Annotated[str | None, Field(pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")] = None
    status: IPStatus = IPStatus.UNKNOWN
    device_type: str | None = None
    description: str | None = None

    @field_validator("address")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IP address format."""
        from netaddr import IPAddress
        try:
            IPAddress(v)
            return v
        except Exception as e:
            raise ValueError(f"Invalid IP address: {e}") from e


class IPAddressCreate(IPAddressBase):
    """IP address creation schema."""

    network_id: str


class IPAddressUpdate(BaseModel):
    """IP address update schema (all fields optional)."""

    hostname: str | None = None
    fqdn: str | None = None
    mac_address: Annotated[str | None, Field(pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")] = None
    status: IPStatus | None = None
    device_type: str | None = None
    description: str | None = None


class IPAddress(IPAddressBase):
    """Complete IP address entity from database."""

    id: str
    network_id: str
    last_seen: datetime | None = None
    discovered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IPAddressBulkCreate(BaseModel):
    """Bulk IP address creation from scan results."""

    network_id: str
    addresses: list[IPAddressCreate]


class IPAddressDiscovered(BaseModel):
    """IP address discovered during a scan."""

    address: str
    mac_address: str | None = None
    hostname: str | None = None
    response_time_ms: float | None = None
    is_alive: bool = True

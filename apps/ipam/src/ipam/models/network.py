"""Network/Subnet models."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from netaddr import IPNetwork


class NetworkBase(BaseModel):
    """Base network fields."""

    name: Annotated[str, Field(min_length=1, max_length=255)]
    network: Annotated[str, Field(description="CIDR notation, e.g., 192.168.1.0/24")]
    vlan_id: Annotated[int | None, Field(ge=1, le=4094)] = None
    description: str | None = None
    location: str | None = None
    gateway: str | None = None
    dns_servers: list[str] | None = None
    is_active: bool = True

    @field_validator("network")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        """Validate CIDR notation."""
        try:
            net = IPNetwork(v)
            # Normalize to network address
            return str(net.cidr)
        except Exception as e:
            raise ValueError(f"Invalid CIDR notation: {e}") from e

    @field_validator("gateway")
    @classmethod
    def validate_gateway(cls, v: str | None) -> str | None:
        """Validate gateway IP address."""
        if v is None:
            return None
        try:
            from netaddr import IPAddress
            IPAddress(v)
            return v
        except Exception as e:
            raise ValueError(f"Invalid IP address: {e}") from e

    @field_validator("dns_servers")
    @classmethod
    def validate_dns_servers(cls, v: list[str] | None) -> list[str] | None:
        """Validate DNS server IP addresses."""
        if v is None:
            return None
        from netaddr import IPAddress
        for ip in v:
            try:
                IPAddress(ip)
            except Exception as e:
                raise ValueError(f"Invalid DNS server IP '{ip}': {e}") from e
        return v


class NetworkCreate(NetworkBase):
    """Network creation schema."""

    pass


class NetworkUpdate(BaseModel):
    """Network update schema (all fields optional)."""

    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    network: str | None = None
    vlan_id: Annotated[int | None, Field(ge=1, le=4094)] = None
    description: str | None = None
    location: str | None = None
    gateway: str | None = None
    dns_servers: list[str] | None = None
    is_active: bool | None = None

    @field_validator("network")
    @classmethod
    def validate_cidr(cls, v: str | None) -> str | None:
        """Validate CIDR notation."""
        if v is None:
            return None
        try:
            net = IPNetwork(v)
            return str(net.cidr)
        except Exception as e:
            raise ValueError(f"Invalid CIDR notation: {e}") from e


class Network(NetworkBase):
    """Complete network entity from database."""

    id: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkWithStats(Network):
    """Network with utilization statistics."""

    total_addresses: int = 0
    used_addresses: int = 0
    utilization_percent: float = 0.0
    last_scan: datetime | None = None

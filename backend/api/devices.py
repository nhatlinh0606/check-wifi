"""
API: Target Device Inspection
Provides on-demand deep diagnostics for candidate router devices.
"""

import ipaddress
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from modules.router_identifier import RouterIdentifier
from modules.network_discovery import NetworkDiscovery

router = APIRouter(prefix="/api/devices", tags=["Devices"])


class InspectRequest(BaseModel):
    ip: str
    mac: Optional[str] = None

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError("Invalid IP address format")


@router.post("/inspect")
def inspect_device(req: InspectRequest) -> Dict[str, Any]:
    """
    Performs deep diagnosis of an IP address (ports, web endpoints, redirect chain, model hints).
    """
    net_disc = NetworkDiscovery()
    gw_info = net_disc.get_default_gateway()
    is_gateway = bool(gw_info and gw_info.get("gateway") == req.ip)

    mac = req.mac
    if not mac:
        arp_table = net_disc.get_arp_table()
        for entry in arp_table:
            if entry["ip"] == req.ip:
                mac = entry["mac"]
                break

    identifier = RouterIdentifier()
    res = identifier.identify_device(
        ip=req.ip,
        mac=mac,
        is_gateway=is_gateway,
        scan_ports=True,
        inspect_web=True
    )

    return res.to_dict()

"""
API: Network Interfaces and Gateway Information
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.network_discovery import NetworkDiscovery

router = APIRouter(prefix="/api/network", tags=["Network"])


class InterfaceResponse(BaseModel):
    name: str
    ip: str
    netmask: str
    cidr: str
    network: str
    mac: str
    is_up: bool
    is_default: bool
    gateway: Optional[str] = None


@router.get("/interfaces", response_model=List[InterfaceResponse])
def get_interfaces():
    nd = NetworkDiscovery()
    ifaces = nd.list_interfaces()
    return [i.to_dict() for i in ifaces]


@router.get("/current", response_model=Optional[InterfaceResponse])
def get_current_interface(interface: Optional[str] = None):
    nd = NetworkDiscovery(interface=interface)
    active = nd.get_active_interface()
    if not active:
        raise HTTPException(status_code=404, detail="No active network interface found")
    return active.to_dict()


@router.get("/gateway")
def get_default_gateway():
    nd = NetworkDiscovery()
    gw = nd.get_default_gateway()
    if not gw:
        raise HTTPException(status_code=404, detail="Default gateway could not be determined")
    return gw

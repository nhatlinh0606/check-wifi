"""
API: Wi-Fi Discovery and Saved Connection Profiles
Uses standard Linux OS APIs (nmcli). Read-only and non-intrusive.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.wifi_service import WifiService

router = APIRouter(prefix="/api/wifi", tags=["Wi-Fi"])
wifi_service = WifiService()


class WifiNetworkResponse(BaseModel):
    ssid: str
    bssid: str
    channel: int
    signal: int
    bars: str
    security: str
    band: str
    vendor: str
    is_tplink: bool


@router.get("/scan", response_model=List[WifiNetworkResponse])
def scan_wifi_networks(rescan: bool = False):
    """
    Discovers nearby Wi-Fi access points using standard operating-system Wi-Fi APIs.
    """
    networks = wifi_service.scan_networks(rescan=rescan)
    return [n.to_dict() for n in networks]


@router.get("/saved-profiles")
def get_saved_profiles() -> List[Dict[str, Any]]:
    """
    Lists Wi-Fi network connection profiles configured on this host machine.
    """
    return wifi_service.get_saved_profiles()

"""
API: Wi-Fi Discovery and Saved Connection Profiles
Uses standard Linux OS APIs (nmcli). Read-only and non-intrusive.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.wifi_service import WifiService
from backend.services.websocket_service import ws_manager

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


class TracePasswordRequest(BaseModel):
    ssid: str
    bssid: Optional[str] = None


class TracePasswordResponse(BaseModel):
    found: bool
    ssid: str
    bssid: Optional[str] = None
    password: Optional[str] = None
    profile_name: Optional[str] = None
    source: Optional[str] = None
    security_type: Optional[str] = None
    message: str
    explanation: Optional[str] = None


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


@router.post("/trace", response_model=TracePasswordResponse)
async def trace_wifi_password(req: TracePasswordRequest):
    """
    Checks if credentials for the selected Wi-Fi network exist in local NetworkManager profiles.
    Never transmits credentials outside this machine.
    """
    result = wifi_service.trace_wifi_password(req.ssid, req.bssid)
    await ws_manager.broadcast("password_trace", result)
    return result

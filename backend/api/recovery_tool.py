"""
API: Wi-Fi Password Recovery Tool Endpoints
Dedicated endpoints for scanning nearby networks, target-specific analysis,
and authorized credential recovery.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.services.wifi_scanner import wifi_scanner, WifiNetwork
from backend.services.recovery_engine import recovery_engine
from backend.services.credential_recovery import credential_recovery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recovery-tool", tags=["Wi-Fi Password Recovery"])


class TracePasswordRequest(BaseModel):
    ssid: str
    bssid: Optional[str] = None
    backup_content: Optional[str] = None
    backup_filename: Optional[str] = None


@router.get("/networks")
def get_nearby_networks(rescan: bool = False) -> List[Dict[str, Any]]:
    """
    Discovers nearby Wi-Fi access points with technical telemetry:
    SSID, BSSID, Signal, Channel, Frequency, Band, Security protocol, Encryption type, Vendor OUI.
    """
    networks = wifi_scanner.scan(rescan=rescan)
    return [n.to_dict() for n in networks]


@router.post("/trace")
async def trace_password(req: TracePasswordRequest) -> Dict[str, Any]:
    """
    Executes a target-specific password recovery analysis across 6 stages.
    Analyzes ONLY the selected network. Never attacks live networks or fabricates results.
    """
    if not req.ssid or not req.ssid.strip():
        raise HTTPException(status_code=400, detail="Target SSID is required.")

    result = await recovery_engine.run_recovery(
        target_ssid=req.ssid,
        target_bssid=req.bssid,
        backup_content=req.backup_content,
        backup_filename=req.backup_filename
    )
    return result.to_dict()


@router.get("/status")
def get_recovery_status() -> Dict[str, Any]:
    """
    Returns the real-time stage progress of the recovery engine.
    """
    return {
        "is_running": recovery_engine.is_running,
        "current_stage": recovery_engine.current_stage,
        "stage_message": recovery_engine.stage_message,
        "stages": recovery_engine.stages_state,
        "has_result": bool(recovery_engine.latest_result),
    }


@router.get("/latest")
def get_latest_recovery_result() -> Dict[str, Any]:
    """
    Returns the most recent recovery result.
    """
    if not recovery_engine.latest_result:
        raise HTTPException(status_code=404, detail="No recovery result available.")
    return recovery_engine.latest_result.to_dict()


@router.post("/upload-backup")
async def upload_backup_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Parses an uploaded router backup or configuration file (.bin, .conf, .xml, .txt)
    to supply legitimate offline recovery material.
    """
    try:
        content_bytes = await file.read()
        filename = file.filename or "uploaded_backup.conf"
        try:
            content_str = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content_str = str(content_bytes)

        return {
            "status": "success",
            "filename": filename,
            "bytes_analyzed": len(content_bytes),
            "content": content_str,
            "message": f"Successfully parsed backup file '{filename}'. You can now run Trace Password with this backup attached."
        }
    except Exception as e:
        logger.error(f"Error parsing uploaded backup file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read backup file: {e}")

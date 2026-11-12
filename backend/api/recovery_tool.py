"""
API: Wi-Fi Password Recovery Tool Endpoints
Dedicated endpoints for scanning nearby networks, target-specific analysis,
authorized credential recovery, and WPA2 packet capture (PCAP/PCAPNG/CAP) inspection.
"""

import base64
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.services.wifi_scanner import wifi_scanner, WifiNetwork
from backend.services.recovery_engine import recovery_engine
from backend.services.credential_recovery import credential_recovery
from backend.services.pcap_analyzer import pcap_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recovery-tool", tags=["Wi-Fi Password Recovery"])


class TracePasswordRequest(BaseModel):
    ssid: str
    bssid: Optional[str] = None
    backup_content: Optional[str] = None
    backup_filename: Optional[str] = None
    pcap_content_base64: Optional[str] = None
    pcap_filename: Optional[str] = None


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

    pcap_bytes = None
    if req.pcap_content_base64:
        try:
            pcap_bytes = base64.b64decode(req.pcap_content_base64)
        except Exception as e:
            logger.warning(f"Failed to decode base64 pcap content: {e}")

    result = await recovery_engine.run_recovery(
        target_ssid=req.ssid,
        target_bssid=req.bssid,
        backup_content=req.backup_content,
        backup_filename=req.backup_filename,
        pcap_bytes=pcap_bytes,
        pcap_filename=req.pcap_filename
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


@router.post("/upload-pcap")
async def upload_pcap_file(
    file: UploadFile = File(...),
    target_ssid: Optional[str] = Form(None),
    target_bssid: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Parses an uploaded WPA2 packet capture (.pcap, .pcapng, .cap) using Scapy.
    Extracts 802.11 beacons, filters 802.1X EAPOL frames, classifies 4-way handshake
    messages (M1-M4), inspects Nonces & Key MICs, and assesses handshake completeness.
    """
    try:
        content_bytes = await file.read()
        filename = file.filename or "capture.pcap"

        # Validate file size (max 50 MB)
        if len(content_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="PCAP file exceeds 50 MB limit.")

        analysis = pcap_analyzer.parse_pcap_bytes(
            data=content_bytes,
            filename=filename,
            target_ssid=target_ssid,
            target_bssid=target_bssid
        )

        b64_content = base64.b64encode(content_bytes).decode("ascii")

        return {
            "status": "success",
            "filename": filename,
            "bytes_analyzed": len(content_bytes),
            "total_packets": analysis.get("total_packets", 0),
            "eapol_packets_count": analysis.get("eapol_packets_count", 0),
            "has_valid_handshake": analysis.get("has_valid_handshake", False),
            "pcap_content_base64": b64_content,
            "analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing uploaded PCAP file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse PCAP file: {e}")

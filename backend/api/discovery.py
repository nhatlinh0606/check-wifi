"""
API: Network Discovery Control & Scan History
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.services.scan_service import scan_manager
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])
history_service = HistoryService()


class StartScanRequest(BaseModel):
    interface: Optional[str] = None
    subnet: Optional[str] = None


@router.post("/start")
async def start_discovery(req: StartScanRequest):
    """
    Triggers an asynchronous background network discovery scan.
    """
    started = await scan_manager.start_scan(interface=req.interface, subnet=req.subnet)
    if not started:
        raise HTTPException(status_code=409, detail="A scan is already in progress")
    return {"message": "Discovery scan started successfully", "status": "running"}


@router.post("/stop")
async def stop_discovery():
    """
    Cancels an active scan.
    """
    cancelled = await scan_manager.cancel_scan()
    if not cancelled:
        raise HTTPException(status_code=400, detail="No active scan to cancel")
    return {"message": "Scan cancelled", "status": "cancelled"}


@router.get("/status")
def get_discovery_status():
    """
    Retrieves current scan progress and discovered devices.
    """
    return scan_manager.get_status()


@router.get("/history")
def list_history() -> List[Dict[str, Any]]:
    """
    Lists past discovery scan reports.
    """
    return history_service.list_history()


@router.get("/history/{report_id}")
def get_history_report(report_id: str):
    """
    Retrieves full details of a past scan report.
    """
    report = history_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Scan report not found")
    return report

"""
API: Autonomous Diagnosis Pipeline
Coordinates the 8-stage network environment discovery, router identification,
management port inspection, credential store audit, and recovery plan generation.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.services.diagnosis_service import diagnosis_manager
from backend.services.credential_service import CredentialRecoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagnosis", tags=["Diagnosis"])


class StartDiagnosisRequest(BaseModel):
    target_interface: Optional[str] = None
    custom_subnet: Optional[str] = None
    imported_backup_content: Optional[str] = None
    imported_backup_filename: Optional[str] = None


@router.get("/status")
def get_diagnosis_status() -> Dict[str, Any]:
    """Returns current real-time diagnosis execution state and stage progress."""
    return diagnosis_manager.get_status()


@router.post("/start")
async def start_diagnosis(request: Optional[StartDiagnosisRequest] = None) -> Dict[str, Any]:
    """Triggers the autonomous 8-stage diagnosis pipeline."""
    target_iface = request.target_interface if request else None
    subnet = request.custom_subnet if request else None
    backup_content = request.imported_backup_content if request else None
    backup_filename = request.imported_backup_filename if request else None

    started = await diagnosis_manager.start_diagnosis(
        target_interface=target_iface,
        custom_subnet=subnet,
        imported_backup_content=backup_content,
        imported_backup_filename=backup_filename
    )

    if not started:
        raise HTTPException(
            status_code=409,
            detail="A diagnosis task is already running. Cancel or wait for it to finish."
        )

    return {
        "status": "started",
        "message": "Autonomous diagnosis initiated.",
        "progress": diagnosis_manager.get_status()
    }


@router.post("/cancel")
@router.post("/stop")
async def cancel_diagnosis() -> Dict[str, Any]:
    """Cancels the currently running diagnosis."""
    cancelled = await diagnosis_manager.cancel_diagnosis()
    if not cancelled:
        return {"status": "ignored", "message": "No running diagnosis to cancel."}
    return {"status": "cancelled", "message": "Diagnosis pipeline cancelled."}


@router.get("/latest")
def get_latest_diagnosis() -> Dict[str, Any]:
    """Returns the most recent completed diagnosis result."""
    if not diagnosis_manager.latest_result:
        # Check if there is an existing report saved on disk
        reports_dir = diagnosis_manager.reports_dir
        if os.path.exists(reports_dir):
            files = sorted(
                [f for f in os.listdir(reports_dir) if f.startswith("diagnosis_") and f.endswith(".json")],
                reverse=True
            )
            if files:
                try:
                    with open(os.path.join(reports_dir, files[0]), "r", encoding="utf-8") as f:
                        diagnosis_manager.latest_result = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load latest saved report: {e}")

    if not diagnosis_manager.latest_result:
        raise HTTPException(status_code=404, detail="No diagnosis report available. Start a new diagnosis.")

    return diagnosis_manager.latest_result


@router.get("/history")
def get_diagnosis_history() -> List[Dict[str, Any]]:
    """Lists saved historical diagnosis reports."""
    reports_dir = diagnosis_manager.reports_dir
    history = []
    if os.path.exists(reports_dir):
        files = sorted(
            [f for f in os.listdir(reports_dir) if f.startswith("diagnosis_") and f.endswith(".json")],
            reverse=True
        )
        for f in files[:20]:
            path = os.path.join(reports_dir, f)
            try:
                stat = os.stat(path)
                with open(path, "r", encoding="utf-8") as rfile:
                    data = json.load(rfile)
                    history.append({
                        "filename": f,
                        "timestamp": data.get("timestamp"),
                        "file_size": stat.st_size,
                        "scenario_id": data.get("recovery_plan", {}).get("scenario_id"),
                        "scenario_title": data.get("recovery_plan", {}).get("scenario_title"),
                        "confidence_rating": data.get("recovery_plan", {}).get("confidence_rating"),
                        "gateway_ip": data.get("routing", {}).get("default_gateway"),
                    })
            except Exception:
                continue
    return history


@router.get("/history/{filename}")
def get_historical_report(filename: str) -> Dict[str, Any]:
    """Retrieves a specific historical diagnosis report."""
    # Prevent directory traversal
    clean_filename = os.path.basename(filename)
    path = os.path.join(diagnosis_manager.reports_dir, clean_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Report {filename} not found.")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {e}")


@router.post("/import-backup")
async def import_backup_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Parses and audits an uploaded router backup or configuration file (.bin, .conf, .xml, .txt, .tar.gz).
    Legitimate recovery source assessment without network intrusion.
    """
    try:
        content_bytes = await file.read()
        filename = file.filename or "uploaded_backup.conf"
        try:
            content_str = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content_str = str(content_bytes)

        # Audit with imported content
        results = CredentialRecoveryService.audit_all_sources(
            imported_backup_content=content_str,
            imported_backup_filename=filename
        )

        return {
            "status": "success",
            "filename": filename,
            "bytes_analyzed": len(content_bytes),
            "sources": [s.to_dict() for s in results],
            "credentials_found": [
                s.to_dict() for s in results if s.matching_credential_found
            ]
        }
    except Exception as e:
        logger.error(f"Failed to parse uploaded backup file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process backup file: {e}")

"""
API: Credential Recovery Assistant
Provides legitimate recovery workflows and hardware reset guides.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from modules.recovery_assistant import RecoveryAssistant, RECOVERY_CASES

router = APIRouter(prefix="/api/recovery", tags=["Recovery"])
assistant = RecoveryAssistant()


@router.get("/cases")
def get_all_recovery_cases() -> Dict[str, Any]:
    """
    Returns all recovery cases (Case A through Case E) with step-by-step procedures.
    """
    return RECOVERY_CASES


@router.get("/cases/{case_id}")
def get_recovery_case(case_id: str) -> Dict[str, Any]:
    """
    Returns instructions for a specific recovery case.
    """
    case = assistant.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found. Valid cases: A, B, C, D, E")
    return case

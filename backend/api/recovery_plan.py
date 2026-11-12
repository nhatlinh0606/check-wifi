"""
API: Recovery Plan & Decision Engine
Delivers deterministic, evidence-based recovery plans across Scenarios 1-5.
Distinguishes confirmed network facts from working hypotheses.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.diagnosis_service import diagnosis_manager
from backend.services.decision_engine import RecoveryDecisionEngine, RecoveryPlan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recovery-plan", tags=["Recovery Plan"])


class CustomEvaluationRequest(BaseModel):
    has_network_connection: bool = False
    connection_type: str = "none"
    gateway_ip: Optional[str] = None
    gateway_mac: Optional[str] = None
    detected_vendor: str = "Unknown"
    is_tplink_candidate: bool = False
    model_hint: Optional[str] = None
    management_endpoints: List[Dict[str, Any]] = []
    credential_sources: List[Dict[str, Any]] = []
    nearby_ssids: List[str] = []
    active_interface_name: Optional[str] = None


@router.get("/latest")
def get_latest_recovery_plan() -> Dict[str, Any]:
    """
    Returns the recovery plan evaluated from the most recent autonomous diagnosis.
    If no diagnosis has been run yet, synthesizes an initial assessment based on current routing.
    """
    if diagnosis_manager.latest_result and "recovery_plan" in diagnosis_manager.latest_result:
        return diagnosis_manager.latest_result["recovery_plan"]

    # Fallback to dynamic on-the-fly evaluation
    plan = RecoveryDecisionEngine.evaluate(
        has_network_connection=False,
        connection_type="none",
        gateway_ip=None,
        gateway_mac=None,
        detected_vendor="Unknown",
        is_tplink_candidate=False,
        model_hint=None,
        management_endpoints=[],
        credential_sources=[],
        nearby_ssids=[],
        active_interface_name=None,
    )
    return plan.to_dict()


@router.post("/evaluate")
def evaluate_custom_state(req: CustomEvaluationRequest) -> Dict[str, Any]:
    """Evaluates a recovery plan for arbitrary or simulated network parameters."""
    plan = RecoveryDecisionEngine.evaluate(
        has_network_connection=req.has_network_connection,
        connection_type=req.connection_type,
        gateway_ip=req.gateway_ip,
        gateway_mac=req.gateway_mac,
        detected_vendor=req.detected_vendor,
        is_tplink_candidate=req.is_tplink_candidate,
        model_hint=req.model_hint,
        management_endpoints=req.management_endpoints,
        credential_sources=req.credential_sources,
        nearby_ssids=req.nearby_ssids,
        active_interface_name=req.active_interface_name,
    )
    return plan.to_dict()


@router.get("/scenarios")
def get_all_scenarios_info() -> List[Dict[str, str]]:
    """Returns documentation on the 5 standard recovery scenarios."""
    return [
        {
            "id": "scenario_1",
            "name": "Scenario 1: Management Web Interface Reachable",
            "description": "Network connection active (LAN/Wi-Fi) and router web portal responds. Next step: Try discovered credentials or perform password reset via official UI/button."
        },
        {
            "id": "scenario_2",
            "name": "Scenario 2: Not Connected over Wi-Fi (No Known Password)",
            "description": "Wi-Fi password unknown; connection cannot be established over air. Passive scanning cannot crack PSK. Next step: Connect an Ethernet cable to bypass Wi-Fi encryption."
        },
        {
            "id": "scenario_3",
            "name": "Scenario 3: Connected over Ethernet (Management IP Changed / Unknown)",
            "description": "Wired link active. If DHCP assigned IP, gateway is found. If no DHCP, sweep private subnets (192.168.0.0/24, 192.168.1.0/24, 10.0.0.0/24, 172.16.0.0/24) to locate router IP."
        },
        {
            "id": "scenario_4",
            "name": "Scenario 4: Router Reachable but Admin Credentials Unknown",
            "description": "IP is known, but admin password is changed and no local credentials exist. Next step: Official factory reset. Includes model-specific reset timings, ISP PPPoE backup warning, and rear hardware reset button guide."
        },
        {
            "id": "scenario_5",
            "name": "Scenario 5: No Usable Recovery Source or Interface Disconnected",
            "description": "No active network link detected and wireless disconnected. Next step: Verify hardware cable and network interface status."
        }
    ]

"""
Unit Tests: Recovery Decision Engine
Verifies deterministic scenario assignment across Scenarios 1 to 5,
facts vs hypotheses separation, hardware reset timings, PoE remote reset, and ISP warnings.
"""

from backend.services.decision_engine import RecoveryDecisionEngine, RecoveryPlan


def test_scenario_1_management_reachable():
    """Scenario 1: Network connected and management web interface responds with saved credentials."""
    plan = RecoveryDecisionEngine.evaluate(
        has_network_connection=True,
        connection_type="ethernet",
        gateway_ip="192.168.0.1",
        gateway_mac="00:1D:0F:11:22:33",
        detected_vendor="TP-Link Corporation",
        is_tplink_candidate=True,
        model_hint="Archer C7",
        management_endpoints=[
            {"url": "http://192.168.0.1", "port": 80, "protocol": "http", "status_code": 200, "title": "TP-Link Archer C7"}
        ],
        credential_sources=[
            {"source_name": "NetworkManager", "status": "Found", "matching_credential_found": True, "credentials": [{"secret": "MySecr3t!"}]}
        ],
        nearby_ssids=["HANH_KIEU_5G"],
        active_interface_name="eth0",
    )

    assert plan.scenario_id == "scenario_1"
    assert "Reachable" in plan.scenario_title
    assert plan.confidence_rating == "High"
    assert any("192.168.0.1" in fact for fact in plan.confirmed_facts)
    assert any("TP-Link" in fact for fact in plan.confirmed_facts)
    assert len(plan.action_steps) > 0


def test_scenario_2_not_connected_wifi():
    """Scenario 2: Not connected, wireless airwaves detect candidate SSIDs."""
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
        nearby_ssids=["HANH_KIEU", "TP-Link_2.4G"],
        active_interface_name="wlp0s20f3",
    )

    assert plan.scenario_id == "scenario_2"
    assert "Not Connected" in plan.scenario_title
    assert any("passive wi-fi" in note.lower() for note in plan.technical_notes)
    # Action step should advise connecting Ethernet
    assert any("ethernet" in (step["instruction"] if isinstance(step, dict) else step.instruction).lower() for step in plan.action_steps)


def test_scenario_3_connected_ethernet_ip_changed():
    """Scenario 3: Connected via Ethernet, but management web interface is not responding."""
    plan = RecoveryDecisionEngine.evaluate(
        has_network_connection=True,
        connection_type="ethernet",
        gateway_ip="192.168.10.1",
        gateway_mac="E8:48:B8:AA:BB:CC",
        detected_vendor="TP-Link",
        is_tplink_candidate=True,
        model_hint=None,
        management_endpoints=[],  # Web UI port not open / closed
        credential_sources=[],
        nearby_ssids=[],
        active_interface_name="eth0",
    )

    assert plan.scenario_id == "scenario_3"
    assert any(
        "subnet" in (step["instruction"] if isinstance(step, dict) else step.instruction).lower()
        or "dhclient" in ((step.get("command") if isinstance(step, dict) else step.command) or "").lower()
        for step in plan.action_steps
    )


def test_scenario_4_reachable_but_creds_unknown():
    """Scenario 4: Router management port is open, but no local credentials found."""
    plan = RecoveryDecisionEngine.evaluate(
        has_network_connection=True,
        connection_type="wifi",
        gateway_ip="192.168.0.1",
        gateway_mac="00:1D:0F:AA:BB:CC",
        detected_vendor="TP-Link",
        is_tplink_candidate=True,
        model_hint="Archer C20",
        management_endpoints=[
            {"url": "http://192.168.0.1", "port": 80, "protocol": "http", "status_code": 200, "title": "TP-Link Login"}
        ],
        credential_sources=[
            {"source_name": "NetworkManager", "status": "Not found", "matching_credential_found": False, "credentials": []}
        ],
        nearby_ssids=[],
        active_interface_name="wlp0s20f3",
    )

    assert plan.scenario_id == "scenario_4"
    assert plan.isp_pppoe_warning is not None
    assert "PPPoE" in plan.isp_pppoe_warning
    assert "VLAN" in plan.isp_pppoe_warning


def test_scenario_5_no_usable_recovery_source():
    """Scenario 5: No link, no wifi SSIDs, interface down."""
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

    assert plan.scenario_id == "scenario_5"
    assert plan.confidence_rating == "Low"
    assert len(plan.unknowns) > 0


def test_poe_remote_reset_and_isp_warning():
    """Verifies outdoor pole-mounted PoE reset button documentation and ISP warning."""
    plan = RecoveryDecisionEngine.evaluate(
        has_network_connection=False,
        connection_type="none",
        gateway_ip=None,
        gateway_mac=None,
        detected_vendor="TP-Link",
        is_tplink_candidate=True,
        model_hint="CPE210",
        management_endpoints=[],
        credential_sources=[],
        nearby_ssids=["HANH_KIEU"],
        active_interface_name="eth0",
    )

    assert plan.poe_remote_reset_guide is not None
    assert plan.poe_remote_reset_guide["applicable"] is True
    assert "Remote Reset" in plan.poe_remote_reset_guide["method"]
    assert "PoE" in plan.poe_remote_reset_guide["indoor_unit"]
    assert "VLAN" in plan.isp_pppoe_warning

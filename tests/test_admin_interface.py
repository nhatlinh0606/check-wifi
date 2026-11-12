import pytest
from modules.admin_interface import AdminInterfaceInspector


def test_extract_title():
    inspector = AdminInterfaceInspector()
    html_raw = "<html><head><title>TP-Link &amp; Technologies Archer AX10</title></head><body></body></html>"
    title = inspector.extract_title(html_raw)
    assert title == "TP-Link & Technologies Archer AX10"


def test_find_tplink_signatures():
    inspector = AdminInterfaceInspector()
    sample = "Welcome to tplinkwifi.net management portal for Archer AX50 router"
    sigs = inspector.find_tplink_signatures(sample)
    assert "tplinkwifi.net" in sigs
    assert any("Archer" in s for s in sigs)


def test_detect_model_hint():
    inspector = AdminInterfaceInspector()
    assert inspector.detect_model_hint("Configuration page for TL-WR841N") == "TL-WR841N"
    assert inspector.detect_model_hint("Deco X20 Mesh System") == "Deco X20"
    assert inspector.detect_model_hint("TP-Link Archer C7 Dual Band") == "Archer C7"
    assert inspector.detect_model_hint("CPE210 PharOS Outdoor AP") == "CPE210"

import pytest
from unittest.mock import patch, MagicMock
from modules.router_identifier import RouterIdentifier
from modules.admin_interface import AdminEndpointInfo
from modules.port_scanner import PortScanResult


@pytest.fixture
def identifier():
    return RouterIdentifier()


def test_mac_oui_lookup_tp_link(identifier):
    # D0:37:45 is a registered TP-LINK OUI
    vendor = identifier.lookup_mac_vendor("D0:37:45:11:22:33")
    assert "TP-LINK" in vendor.upper()


def test_mac_oui_lookup_unknown(identifier):
    # Locally administered or unallocated prefix returns Unknown
    vendor = identifier.lookup_mac_vendor("02:00:00:11:22:33")
    assert vendor == "Unknown"
    assert identifier.lookup_mac_vendor(None) == "Unknown"


def test_identify_tplink_high_confidence(identifier):
    # Simulated TP-Link Archer router
    with patch.object(identifier.port_scanner, "scan_host") as mock_ports, \
         patch.object(identifier.admin_inspector, "inspect_host") as mock_web:

        mock_ports.return_value = [
            PortScanResult(port=80, service="HTTP", is_open=True, latency_ms=1.2),
            PortScanResult(port=443, service="HTTPS", is_open=True, latency_ms=1.5)
        ]
        mock_web.return_value = [
            AdminEndpointInfo(
                url="http://192.168.0.1/",
                port=80,
                protocol="http",
                status_code=200,
                title="TP-Link Wireless Router Archer AX50",
                server_header="TP-Link HTTP Server",
                redirect_chain=[],
                final_url="http://192.168.0.1/webpages/login.html",
                auth_realm=None,
                tplink_signatures_found=["TP-Link", "Archer AX50"],
                model_hint="Archer AX50"
            )
        ]

        res = identifier.identify_device(
            ip="192.168.0.1",
            mac="D0:37:45:aa:bb:cc",
            is_gateway=True,
            scan_ports=True,
            inspect_web=True
        )

        assert res.is_tplink_candidate is True
        assert res.confidence == "High"
        assert res.confidence_score >= 65
        assert res.model_hint == "Archer AX50"
        assert res.admin_url == "http://192.168.0.1/webpages/login.html"


def test_identify_third_party_zte_gateway(identifier):
    # Simulated ZTE GPON ONT
    with patch.object(identifier.port_scanner, "scan_host") as mock_ports, \
         patch.object(identifier.admin_inspector, "inspect_host") as mock_web:

        mock_ports.return_value = [
            PortScanResult(port=80, service="HTTP", is_open=True, latency_ms=1.2)
        ]
        mock_web.return_value = [
            AdminEndpointInfo(
                url="http://192.168.1.1/",
                port=80,
                protocol="http",
                status_code=200,
                title="F6601P",
                server_header=None,
                redirect_chain=[],
                final_url="https://192.168.1.1/",
                auth_realm=None,
                tplink_signatures_found=[],
                model_hint=None
            )
        ]

        res = identifier.identify_device(
            ip="192.168.1.1",
            mac="58:D3:12:ef:86:57",
            is_gateway=True,
            scan_ports=True,
            inspect_web=True
        )

        assert res.is_tplink_candidate is False
        assert res.confidence in ("None", "Low")
        assert res.detected_vendor == "ZTE"

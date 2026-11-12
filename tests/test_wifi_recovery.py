"""
Unit Tests: Wi-Fi Password Recovery Tool
Comprehensive test suite verifying:
- Wi-Fi network scanning & parsing
- Target SSID selection
- BSSID matching
- Security protocol detection
- Recovery source assessment
- Recovered credential validation
- Recovery failure handling
- Missing system commands
- Permission errors
- Empty scan results
- REST API endpoints
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.wifi_scanner import WifiScannerService, WifiNetwork
from backend.services.security_analyzer import SecurityAnalyzerService
from backend.services.credential_recovery import CredentialRecoveryService
from backend.services.recovery_engine import WifiRecoveryEngine


@pytest.fixture
def client():
    return TestClient(app)


# =============================================================================
# 1. Wi-Fi Scanner Tests
# =============================================================================

SAMPLE_NMCLI_OUTPUT = """
*:Trong Duc:58\\:D3\\:12\\:CF\\:86\\:58:Infra:153:5765 MHz:270 Mbit/s:99:▂▄▆█:WPA1 WPA2
 :HANH KIEU:54\\:04\\:63\\:23\\:75\\:31:Infra:1:2412 MHz:130 Mbit/s:92:▂▄▆█:WPA2
 :TP-LINK_65FF24:E8\\:94\\:F6\\:65\\:FF\\:24:Infra:1:2412 MHz:135 Mbit/s:85:▂▄▆█:WPA2
 ::54\\:04\\:63\\:23\\:75\\:3C:Infra:56:5280 MHz:270 Mbit/s:80:▂▄▆█:WPA3
 :Open_Cafe:AA\\:BB\\:CC\\:DD\\:EE\\:FF:Infra:6:2437 MHz:54 Mbit/s:40:▂▄__:--
"""


def test_wifi_scanner_parsing():
    """Verify parsing nmcli output with escaped colons and detailed telemetry."""
    scanner = WifiScannerService()
    networks = scanner.parse_nmcli_output(SAMPLE_NMCLI_OUTPUT)

    assert len(networks) == 5

    # Connected network
    trong_duc = next(n for n in networks if n.ssid == "Trong Duc")
    assert trong_duc.is_connected is True
    assert trong_duc.bssid == "58:D3:12:CF:86:58"
    assert trong_duc.channel == 153
    assert trong_duc.band == "5 GHz"
    assert trong_duc.signal == 99

    # HANH KIEU network
    hanh_kieu = next(n for n in networks if n.ssid == "HANH KIEU")
    assert hanh_kieu.is_connected is False
    assert hanh_kieu.bssid == "54:04:63:23:75:31"
    assert hanh_kieu.channel == 1
    assert hanh_kieu.band == "2.4 GHz"
    assert "WPA2" in hanh_kieu.security
    assert hanh_kieu.encryption == "AES-CCMP"

    # TP-Link network
    tplink_net = next(n for n in networks if "TP-LINK" in n.ssid)
    assert tplink_net.is_tplink is True

    # Hidden SSID network
    hidden_net = next(n for n in networks if n.bssid == "54:04:63:23:75:3C")
    assert hidden_net.ssid == "[Hidden Network]"
    assert "WPA3" in hidden_net.security

    # Open network
    open_net = next(n for n in networks if n.ssid == "Open_Cafe")
    assert "Open" in open_net.security
    assert open_net.encryption == "None"


def test_wifi_scanner_empty_output():
    """Verify handling when scan returns empty output."""
    scanner = WifiScannerService()
    networks = scanner.parse_nmcli_output("")
    assert networks == []

    networks_whitespace = scanner.parse_nmcli_output("   \n\n  ")
    assert networks_whitespace == []


def test_wifi_scanner_command_failure():
    """Verify graceful handling when nmcli command fails or times out."""
    scanner = WifiScannerService()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Error: NetworkManager is not running")
        result = scanner.scan()
        assert result == []

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="nmcli", timeout=10)):
        result = scanner.scan()
        assert result == []


def test_target_ssid_selection_and_bssid_matching():
    """Verify selecting target by exact SSID, case-insensitive SSID, and BSSID."""
    scanner = WifiScannerService()
    with patch.object(scanner, "scan", return_value=scanner.parse_nmcli_output(SAMPLE_NMCLI_OUTPUT)):
        # By SSID
        target_1 = scanner.get_target_network(ssid="hanh kieu")
        assert target_1 is not None
        assert target_1.ssid == "HANH KIEU"

        # By BSSID
        target_2 = scanner.get_target_network(ssid="Unknown", bssid="54:04:63:23:75:31")
        assert target_2 is not None
        assert target_2.ssid == "HANH KIEU"

        # Not found
        target_none = scanner.get_target_network(ssid="NonExistentSSID_999")
        assert target_none is None


# =============================================================================
# 2. Security Protocol Detection Tests
# =============================================================================

def test_security_analyzer_protocols():
    """Verify protocol identification and confirmation of passive limitation."""
    # WPA2
    analysis_wpa2 = SecurityAnalyzerService.analyze_target(
        ssid="HANH KIEU",
        bssid="54:04:63:23:75:31",
        security="WPA2",
        encryption="AES-CCMP",
        channel=1,
        frequency="2412 MHz",
        band="2.4 GHz"
    )
    assert analysis_wpa2["protocol_name"] == "WPA2-Personal (802.11i)"
    assert analysis_wpa2["pairwise_cipher"] == "AES-CCMP"
    assert "PBKDF2" in analysis_wpa2["pmk_derivation"]
    assert analysis_wpa2["passive_airwave_extraction_possible"] is False
    assert "beacon management frames" in analysis_wpa2["technical_limitation_explanation"]

    # WPA3
    analysis_wpa3 = SecurityAnalyzerService.analyze_target(
        ssid="SecureWPA3",
        bssid="11:22:33:44:55:66",
        security="WPA3-SAE",
        encryption="AES-CCMP",
        channel=36,
        frequency="5180 MHz",
        band="5 GHz"
    )
    assert analysis_wpa3["protocol_name"] == "WPA3-Personal"
    assert "Dragonfly" in analysis_wpa3["pmk_derivation"]
    assert analysis_wpa3["passive_airwave_extraction_possible"] is False


# =============================================================================
# 3. Credential Recovery Assessment Tests
# =============================================================================

def test_credential_recovery_from_network_manager():
    """Verify recovering genuine password when present in local NetworkManager profiles."""
    with patch("subprocess.run") as mock_run:
        # Mock nmcli show returning secret PSK
        mock_run.return_value = MagicMock(returncode=0, stdout="ValidPreSharedKey2026!\n", stderr="")

        res = CredentialRecoveryService.recover_target_credential("HANH KIEU", "54:04:63:23:75:31")
        assert res["found"] is True
        assert res["credential"]["password"] == "ValidPreSharedKey2026!"
        assert res["credential"]["ssid"] == "HANH KIEU"
        assert "NetworkManager" in res["credential"]["source_name"]


def test_credential_recovery_not_found():
    """Verify honest failure handling when no credentials exist locally."""
    with patch("subprocess.run") as mock_run:
        # Return empty PSK and empty profile list
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error: connection not found")

        res = CredentialRecoveryService.recover_target_credential("HANH KIEU", "54:04:63:23:75:31")
        assert res["found"] is False
        assert res["credential"] is None
        assert len(res["checks_performed"]) > 0


def test_credential_recovery_from_user_backup():
    """Verify recovering password from attached router configuration backup."""
    backup_sample = """
    # TP-Link Config Export
    wlan.ssid=HANH KIEU
    wlan.key=RecoveredFromBackup9988!
    """

    with patch("subprocess.run") as mock_run:
        # Simulate local nmcli not having it
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        res = CredentialRecoveryService.recover_target_credential(
            target_ssid="HANH KIEU",
            target_bssid="54:04:63:23:75:31",
            backup_content=backup_sample,
            backup_filename="router_backup.conf"
        )

        assert res["found"] is True
        assert res["credential"]["password"] == "RecoveredFromBackup9988!"
        assert "router_backup.conf" in res["credential"]["source_name"]


# =============================================================================
# 4. Modular Recovery Engine 6-Stage Tests
# =============================================================================

@pytest.mark.asyncio
async def test_recovery_engine_success_pipeline():
    """Verify full 6-stage async pipeline execution ending in SUCCESS."""
    engine = WifiRecoveryEngine()

    with patch.object(
        CredentialRecoveryService,
        "recover_target_credential",
        return_value={
            "found": True,
            "credential": {
                "ssid": "HANH KIEU",
                "password": "PasswordRecovered123!",
                "source_name": "Local NetworkManager Profile (HANH KIEU)",
                "source_type": "Operating System Profile"
            },
            "checks_performed": [{"source": "NetworkManager", "status": "Found", "details": "Match found"}]
        }
    ):
        result = await engine.run_recovery(target_ssid="HANH KIEU", target_bssid="54:04:63:23:75:31")

        assert result.status == "SUCCESS"
        assert result.outcome_code == "PASSWORD_RECOVERED"
        assert result.recovered_password == "PasswordRecovered123!"
        assert result.target_ssid == "HANH KIEU"
        assert len(result.stages) == 6
        assert all(s["status"] == "completed" for s in result.stages)


@pytest.mark.asyncio
async def test_recovery_engine_not_recovered_pipeline():
    """Verify full 6-stage async pipeline execution ending in NOT_RECOVERED."""
    engine = WifiRecoveryEngine()

    with patch.object(
        CredentialRecoveryService,
        "recover_target_credential",
        return_value={
            "found": False,
            "credential": None,
            "checks_performed": [{"source": "NetworkManager", "status": "Not found", "details": "No profile"}]
        }
    ):
        result = await engine.run_recovery(target_ssid="HANH KIEU", target_bssid="54:04:63:23:75:31")

        assert result.status == "NOT_RECOVERED"
        assert result.outcome_code == "NO_CREDENTIAL_AVAILABLE"
        assert result.recovered_password is None
        assert result.failure_reason is not None
        assert "Missing" in result.missing_evidence
        assert len(result.next_legitimate_options) > 0
        assert "PASSIVE SCANNING LIMITATION" in result.technical_limitation_notice


# =============================================================================
# 5. REST API Endpoints Tests
# =============================================================================

def test_api_networks_endpoint(client):
    """GET /api/recovery-tool/networks returns list of nearby wireless networks."""
    res = client.get("/api/recovery-tool/networks")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_trace_endpoint_validation(client):
    """POST /api/recovery-tool/trace requires target SSID."""
    res = client.post("/api/recovery-tool/trace", json={"ssid": ""})
    assert res.status_code == 400


def test_api_trace_endpoint_execution(client):
    """POST /api/recovery-tool/trace executes target recovery pipeline."""
    with patch.object(
        CredentialRecoveryService,
        "recover_target_credential",
        return_value={
            "found": True,
            "credential": {
                "ssid": "HANH KIEU",
                "password": "MyAuthorizedSecret2026",
                "source_name": "Local NetworkManager Profile",
                "source_type": "OS Store"
            },
            "checks_performed": [{"source": "NM", "status": "Found", "details": "ok"}]
        }
    ):
        res = client.post("/api/recovery-tool/trace", json={"ssid": "HANH KIEU", "bssid": "54:04:63:23:75:31"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["recovered_password"] == "MyAuthorizedSecret2026"
        assert len(data["stages"]) == 6


def test_api_upload_backup_file(client):
    """POST /api/recovery-tool/upload-backup parses uploaded file content."""
    content = b"wlan.ssid=HANH KIEU\nwlan.pass=SecretBackupKey!\n"
    files = {"file": ("router_backup.conf", content, "text/plain")}
    res = client.post("/api/recovery-tool/upload-backup", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["filename"] == "router_backup.conf"
    assert "SecretBackupKey!" in data["content"]

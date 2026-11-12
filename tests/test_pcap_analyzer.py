"""
Unit Tests: WPA2 Packet Capture & 4-Way Handshake Analyzer
Tests Scapy-based PCAP/PCAPNG parsing, EAPOL frame identification,
4-way handshake message classification (M1-M4), Nonce/MIC extraction,
and handshake completeness assessment.
"""

import base64
import pytest
import tempfile
from fastapi.testclient import TestClient

from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt
from scapy.layers.l2 import Ether, LLC, SNAP
from scapy.layers.eap import EAPOL, EAPOL_KEY
from scapy.utils import wrpcap

from backend.main import app
from backend.services.pcap_analyzer import pcap_analyzer
from backend.services.recovery_engine import WifiRecoveryEngine


@pytest.fixture
def client():
    return TestClient(app)


def create_synthetic_handshake_bytes(
    include_m1: bool = True,
    include_m2: bool = True,
    include_m3: bool = False,
    include_m4: bool = False,
    ap_mac: str = "54:04:63:23:75:31",
    sta_mac: str = "A4:C3:F0:12:34:56",
    ssid: str = "Corporate-Secure",
    anonce: bytes = b"\x11" * 32,
    snonce: bytes = b"\x22" * 32,
    mic: bytes = b"\x33" * 16,
) -> bytes:
    """Builds synthetic IEEE 802.11 beacon and EAPOL-Key frames in PCAP format."""
    packets = []

    # 1. Dot11 Beacon frame
    beacon = (
        Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff", addr2=ap_mac.lower(), addr3=ap_mac.lower())
        / Dot11Beacon(cap="ESS")
        / Dot11Elt(ID=0, info=ssid.encode("utf-8"))
    )
    packets.append(beacon)

    # 2. EAPOL Message 1 (AP -> STA, Pairwise, Ack=1, MIC=0)
    if include_m1:
        m1 = (
            Dot11(type=2, subtype=0, FCfield="from_DS", addr1=sta_mac.lower(), addr2=ap_mac.lower(), addr3=ap_mac.lower())
            / LLC(dsap=0xAA, ssap=0xAA, ctrl=3)
            / SNAP(OUI=0x000000, code=0x888E)
            / EAPOL(version=1, type=3)
            / EAPOL_KEY(
                key_descriptor_type=2,
                key_descriptor_type_version=2,
                key_type=1,
                key_ack=1,
                has_key_mic=0,
                install=0,
                secure=0,
                key_replay_counter=1,
                key_nonce=anonce,
                key_mic=b"\x00" * 16,
            )
        )
        packets.append(m1)

    # 3. EAPOL Message 2 (STA -> AP, Pairwise, Ack=0, MIC=1)
    if include_m2:
        m2 = (
            Dot11(type=2, subtype=0, FCfield="to_DS", addr1=ap_mac.lower(), addr2=sta_mac.lower(), addr3=ap_mac.lower())
            / LLC(dsap=0xAA, ssap=0xAA, ctrl=3)
            / SNAP(OUI=0x000000, code=0x888E)
            / EAPOL(version=1, type=3)
            / EAPOL_KEY(
                key_descriptor_type=2,
                key_descriptor_type_version=2,
                key_type=1,
                key_ack=0,
                has_key_mic=1,
                install=0,
                secure=0,
                key_replay_counter=1,
                key_nonce=snonce,
                key_mic=mic,
            )
        )
        packets.append(m2)

    # 4. EAPOL Message 3 (AP -> STA, Pairwise, Ack=1, MIC=1, Install=1)
    if include_m3:
        m3 = (
            Dot11(type=2, subtype=0, FCfield="from_DS", addr1=sta_mac.lower(), addr2=ap_mac.lower(), addr3=ap_mac.lower())
            / LLC(dsap=0xAA, ssap=0xAA, ctrl=3)
            / SNAP(OUI=0x000000, code=0x888E)
            / EAPOL(version=1, type=3)
            / EAPOL_KEY(
                key_descriptor_type=2,
                key_descriptor_type_version=2,
                key_type=1,
                key_ack=1,
                has_key_mic=1,
                install=1,
                secure=0,
                key_replay_counter=2,
                key_nonce=anonce,
                key_mic=b"\x44" * 16,
            )
        )
        packets.append(m3)

    # 5. EAPOL Message 4 (STA -> AP, Pairwise, Ack=0, MIC=1, Secure=1)
    if include_m4:
        m4 = (
            Dot11(type=2, subtype=0, FCfield="to_DS", addr1=ap_mac.lower(), addr2=sta_mac.lower(), addr3=ap_mac.lower())
            / LLC(dsap=0xAA, ssap=0xAA, ctrl=3)
            / SNAP(OUI=0x000000, code=0x888E)
            / EAPOL(version=1, type=3)
            / EAPOL_KEY(
                key_descriptor_type=2,
                key_descriptor_type_version=2,
                key_type=1,
                key_ack=0,
                has_key_mic=1,
                install=0,
                secure=1,
                key_replay_counter=2,
                key_nonce=b"\x00" * 32,
                key_mic=b"\x55" * 16,
            )
        )
        packets.append(m4)

    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
        wrpcap(tf.name, packets)
        tmp_path = tf.name

    with open(tmp_path, "rb") as f:
        data = f.read()

    return data


# =============================================================================
# 1. PCAP Parsing & Classification Tests
# =============================================================================


def test_complete_4way_handshake():
    """Verify parsing and classification of a complete M1-M4 4-way handshake."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=True,
        include_m3=True,
        include_m4=True,
        ap_mac="54:04:63:23:75:31",
        sta_mac="A4:C3:F0:12:34:56",
        ssid="HANH KIEU",
    )

    result = pcap_analyzer.parse_pcap_bytes(pcap_data, "four_way.pcap", target_ssid="HANH KIEU")

    assert result["status"] == "PARSED_SUCCESS"
    assert result["total_packets"] == 5  # 1 beacon + 4 EAPOL
    assert result["eapol_packets_count"] == 4
    assert result["has_valid_handshake"] is True

    best = result["best_handshake"]
    assert best is not None
    assert best["completeness"] == "COMPLETE_4WAY"
    assert best["is_usable_for_offline_validation"] is True
    assert best["ap_mac"] == "54:04:63:23:75:31"
    assert best["sta_mac"] == "A4:C3:F0:12:34:56"
    assert best["associated_ssid"] == "HANH KIEU"
    assert set(best["messages_found"]) == {"M1", "M2", "M3", "M4"}
    assert best["anonce_hex"] == "11" * 32
    assert best["snonce_hex"] == "22" * 32
    assert best["key_mic_hex"] == "33" * 16
    assert best["mic_algorithm"] == "HMAC-SHA1-128 (AES-128-CCMP)"


def test_valid_handshake_pair_m1_m2():
    """Verify that M1 + M2 pair is recognized as valid for cryptographic key verification."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=True,
        include_m3=False,
        include_m4=False,
    )

    result = pcap_analyzer.parse_pcap_bytes(pcap_data, "pair.pcap")

    assert result["status"] == "PARSED_SUCCESS"
    assert result["eapol_packets_count"] == 2
    assert result["has_valid_handshake"] is True

    best = result["best_handshake"]
    assert best["completeness"] == "VALID_HANDSHAKE_PAIR"
    assert best["is_usable_for_offline_validation"] is True
    assert "M1" in best["messages_found"]
    assert "M2" in best["messages_found"]
    assert best["anonce_hex"] == "11" * 32
    assert best["snonce_hex"] == "22" * 32
    assert best["key_mic_hex"] == "33" * 16


def test_incomplete_handshake_m1_only():
    """Verify that M1 only without client response M2 is marked incomplete."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=False,
        include_m3=False,
        include_m4=False,
    )

    result = pcap_analyzer.parse_pcap_bytes(pcap_data, "m1_only.pcap")

    assert result["status"] == "PARSED_SUCCESS"
    assert result["eapol_packets_count"] == 1
    assert result["has_valid_handshake"] is False

    best = result["best_handshake"]
    assert best["completeness"] == "INCOMPLETE_HANDSHAKE"
    assert best["is_usable_for_offline_validation"] is False
    assert best["messages_found"] == ["M1"]
    assert best["snonce_hex"] is None
    assert "missing" in best["cryptographic_summary"].lower()


def test_incomplete_handshake_m2_only():
    """Verify that M2 only without AP ANonce is marked incomplete."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=False,
        include_m2=True,
        include_m3=False,
        include_m4=False,
    )

    result = pcap_analyzer.parse_pcap_bytes(pcap_data, "m2_only.pcap")

    assert result["status"] == "PARSED_SUCCESS"
    assert result["eapol_packets_count"] == 1
    assert result["has_valid_handshake"] is False

    best = result["best_handshake"]
    assert best["completeness"] == "INCOMPLETE_HANDSHAKE"
    assert best["is_usable_for_offline_validation"] is False


def test_non_eapol_pcap():
    """Verify handling of PCAP capture that has no EAPOL packets."""
    packets = [Ether(src="00:11:22:33:44:55", dst="ff:ff:ff:ff:ff:ff")]
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tf:
        wrpcap(tf.name, packets)
        tmp_path = tf.name

    with open(tmp_path, "rb") as f:
        data = f.read()

    result = pcap_analyzer.parse_pcap_bytes(data, "ethernet_only.pcap")

    assert result["status"] == "PARSED_SUCCESS"
    assert result["total_packets"] == 1
    assert result["eapol_packets_count"] == 0
    assert result["has_valid_handshake"] is False
    assert result["best_handshake"] is None


def test_corrupt_pcap_data():
    """Verify robust handling of corrupted or truncated bytes."""
    corrupt_data = b"NOT_A_VALID_PCAP_HEADER_1234567890"
    result = pcap_analyzer.parse_pcap_bytes(corrupt_data, "corrupt.pcap")

    assert result["status"] == "ERROR"
    assert "Invalid or corrupted PCAP capture" in result["error"]
    assert result["eapol_packets_count"] == 0


# =============================================================================
# 2. Recovery Engine PCAP Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_recovery_engine_with_valid_handshake():
    """
    Verify that providing a PCAP with a valid 4-way handshake yields
    outcome HANDSHAKE_EVIDENCE_AVAILABLE, status HANDSHAKE_CAPTURED,
    and correctly clarifies that plaintext password is NOT recovered.
    """
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=True,
        ap_mac="54:04:63:23:75:31",
        ssid="HANH KIEU",
    )

    engine = WifiRecoveryEngine()
    result = await engine.run_recovery(
        target_ssid="HANH KIEU",
        target_bssid="54:04:63:23:75:31",
        pcap_bytes=pcap_data,
        pcap_filename="test_handshake.pcap",
    )

    assert result.status == "HANDSHAKE_CAPTURED"
    assert result.outcome_code == "HANDSHAKE_EVIDENCE_AVAILABLE"
    # Crucial verification: Handshake does NOT expose the plaintext password!
    assert result.recovered_password is None
    assert result.handshake_evidence is not None
    assert result.handshake_evidence["completeness"] == "VALID_HANDSHAKE_PAIR"
    assert result.handshake_evidence["anonce_hex"] == "11" * 32
    assert result.handshake_evidence["snonce_hex"] == "22" * 32
    assert result.handshake_evidence["key_mic_hex"] == "33" * 16

    # Verify checks_performed includes PCAP inspection
    pcap_chk = next(
        (c for c in result.checks_performed if c.get("source_id") == "pcap_packet_capture"),
        None,
    )
    assert pcap_chk is not None
    assert pcap_chk["status"] == "FOUND"
    assert pcap_chk["evidence_found"] is True


@pytest.mark.asyncio
async def test_recovery_engine_with_incomplete_handshake():
    """Verify that providing M1 only yields HANDSHAKE_EVIDENCE_INCOMPLETE."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=False,
    )

    engine = WifiRecoveryEngine()
    result = await engine.run_recovery(
        target_ssid="Corporate-Secure",
        pcap_bytes=pcap_data,
        pcap_filename="m1_partial.pcap",
    )

    assert result.status == "NOT_RECOVERED"
    assert result.outcome_code == "HANDSHAKE_EVIDENCE_INCOMPLETE"
    assert result.recovered_password is None


# =============================================================================
# 3. REST API Endpoint Tests
# =============================================================================


def test_api_upload_pcap_endpoint(client):
    """Test POST /api/recovery-tool/upload-pcap endpoint."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=True,
        ap_mac="54:04:63:23:75:31",
        ssid="TestLab",
    )

    response = client.post(
        "/api/recovery-tool/upload-pcap",
        files={"file": ("test.pcap", pcap_data, "application/vnd.tcpdump.pcap")},
        data={"target_ssid": "TestLab"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "test.pcap"
    assert data["eapol_packets_count"] == 2
    assert data["has_valid_handshake"] is True
    assert "pcap_content_base64" in data
    assert data["analysis"]["best_handshake"]["completeness"] == "VALID_HANDSHAKE_PAIR"


def test_api_trace_with_pcap_base64(client):
    """Test POST /api/recovery-tool/trace with base64 encoded PCAP capture."""
    pcap_data = create_synthetic_handshake_bytes(
        include_m1=True,
        include_m2=True,
        ap_mac="54:04:63:23:75:31",
        ssid="HANH KIEU",
    )
    b64_pcap = base64.b64encode(pcap_data).decode("ascii")

    response = client.post(
        "/api/recovery-tool/trace",
        json={
            "ssid": "HANH KIEU",
            "bssid": "54:04:63:23:75:31",
            "pcap_content_base64": b64_pcap,
            "pcap_filename": "client_capture.pcap",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HANDSHAKE_CAPTURED"
    assert data["outcome_code"] == "HANDSHAKE_EVIDENCE_AVAILABLE"
    assert data["target_ssid"] == "HANH KIEU"
    assert data["recovered_password"] is None  # Plaintext password is NOT in passive capture!
    assert data["handshake_evidence"] is not None
    assert data["handshake_evidence"]["anonce_hex"] == "11" * 32
    assert data["handshake_evidence"]["snonce_hex"] == "22" * 32

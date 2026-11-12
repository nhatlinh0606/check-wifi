import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_interfaces():
    response = client.get("/api/network/interfaces")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_gateway():
    response = client.get("/api/network/gateway")
    # Might be 200 if route exists, or 404 in isolated environment
    assert response.status_code in (200, 404)


def test_wifi_scan_endpoint():
    response = client.get("/api/wifi/scan?rescan=false")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_trace_wifi_password_endpoint():
    # Test unsaved network
    response = client.post("/api/wifi/trace", json={"ssid": "NonExistentWifiTestSSID123", "bssid": "00:11:22:33:44:55"})
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is False
    assert "Password not found in local saved Wi-Fi profiles" in data["message"]
    assert "explanation" in data


def test_discovery_status():
    response = client.get("/api/discovery/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "progress" in data
    assert "discovered_devices" in data


def test_recovery_cases():
    response = client.get("/api/recovery/cases")
    assert response.status_code == 200
    cases = response.json()
    assert "A" in cases
    assert "E" in cases


def test_invalid_ip_inspect():
    response = client.post("/api/devices/inspect", json={"ip": "invalid-ip"})
    assert response.status_code == 422

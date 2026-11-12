"""
Unit Tests: Diagnosis Service & Autonomous API Endpoints
Verifies 8-stage execution, credential auditing, file backup parsing, and REST endpoints.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.diagnosis_service import DiagnosisService, DIAGNOSIS_STAGES
from backend.services.credential_service import CredentialRecoveryService


@pytest.fixture
def client():
    return TestClient(app)


def test_diagnosis_stages_count():
    """Verify all 8 pipeline stages are configured."""
    assert len(DIAGNOSIS_STAGES) == 8


def test_diagnosis_service_initial_state():
    """Verify diagnosis service initial state."""
    svc = DiagnosisService(reports_dir="/tmp/test_reports")
    status = svc.get_status()
    assert status["status"] == "idle"
    assert status["current_stage"] == 0
    assert len(status["stages"]) == 8


def test_credential_service_backup_audit():
    """Verify backup parser audits plaintext / key-value configuration exports."""
    sample_backup = """
    # TP-Link Router Configuration Export
    sys.model=TL-WR841N
    lan.ip=192.168.0.1
    lan.mask=255.255.255.0
    wlan.ssid=HANH_KIEU_WIFI
    wlan.key=SecretPassw0rd123!
    admin.user=admin
    admin.pass=admin9988
    """
    sources = CredentialRecoveryService.audit_all_sources(
        target_ssid="HANH_KIEU_WIFI",
        imported_backup_content=sample_backup,
        imported_backup_filename="test_backup.conf"
    )

    assert len(sources) > 0
    uploaded_source = next((s for s in sources if s.source_id == "user_backup"), None)
    assert uploaded_source is not None
    assert uploaded_source.status == "Found"
    assert uploaded_source.matching_credential_found is True
    assert uploaded_source.recovered_data is not None


def test_api_diagnosis_status(client):
    """GET /api/diagnosis/status returns valid schema."""
    res = client.get("/api/diagnosis/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "stages" in data
    assert len(data["stages"]) == 8


def test_api_recovery_plan_latest(client):
    """GET /api/recovery-plan/latest returns plan structure."""
    res = client.get("/api/recovery-plan/latest")
    assert res.status_code == 200
    data = res.json()
    assert "scenario_id" in data
    assert "scenario_title" in data
    assert "action_steps" in data
    assert "confirmed_facts" in data


def test_api_recovery_scenarios(client):
    """GET /api/recovery-plan/scenarios returns documentation on all 5 scenarios."""
    res = client.get("/api/recovery-plan/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 5
    ids = [s["id"] for s in scenarios]
    assert "scenario_1" in ids
    assert "scenario_2" in ids
    assert "scenario_3" in ids
    assert "scenario_4" in ids
    assert "scenario_5" in ids


def test_api_import_backup_endpoint(client):
    """POST /api/diagnosis/import-backup uploads and audits configuration file."""
    sample_content = b"wlan_ssid=HANH_KIEU\nwlan_key=RecoveredKey2026\n"
    files = {"file": ("backup.conf", sample_content, "text/plain")}
    res = client.post("/api/diagnosis/import-backup", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["filename"] == "backup.conf"
    assert "sources" in data

import pytest
from fastapi.testclient import TestClient
from backend.services.auditor_service import AuditorService
from backend.main import app

client = TestClient(app)


def test_entropy_calculation():
    # Empty string
    assert AuditorService.calculate_entropy("") == 0.0
    # 8-digit numeric: 8 * log2(10) ~= 26.58
    entropy_num = AuditorService.calculate_entropy("12345678")
    assert 26.0 <= entropy_num <= 27.0
    # 16-char complex
    entropy_complex = AuditorService.calculate_entropy("A#b9!xL@2$kP%4wZ")
    assert entropy_complex > 80.0


def test_weak_pattern_detection():
    # Sequential numbers
    warnings = AuditorService.detect_weak_patterns("abc123456")
    assert any("sequential" in w.lower() for w in warnings)

    # Pure numeric
    warnings = AuditorService.detect_weak_patterns("0943561541")
    assert any("digits only" in w.lower() for w in warnings)

    # Short length
    warnings = AuditorService.detect_weak_patterns("short")
    assert any("under 8" in w for w in warnings)

    # Repeated chars
    warnings = AuditorService.detect_weak_patterns("password1111")
    assert any("repeated" in w.lower() for w in warnings)


def test_password_generation():
    pwd = AuditorService.generate_password(length=20, include_symbols=True)
    assert len(pwd) == 20
    assert any(c.isdigit() for c in pwd)
    assert any(c.isalpha() for c in pwd)


def test_wordlist_analysis():
    sample_text = """password123
admin
12345678
password123
StrongP@ssw0rd!2026
12345678
"""
    result = AuditorService.analyze_wordlist_text(sample_text)
    assert result["total_entries"] == 6
    assert result["unique_entries"] == 4
    assert result["duplicate_count"] == 2
    assert result["pure_numeric_count"] >= 2


def test_search_space_simulation():
    sim = AuditorService.simulate_search_space(
        charset_type="numeric",
        length=8,
        attempts_per_sec=1000.0
    )
    assert sim["pool_size"] == 10
    assert sim["length"] == 8
    # 10^8 = 100,000,000 combinations
    assert "100,000,000" in sim["total_combinations_exact"]


# API Endpoints Integration Tests
def test_api_analyze_password():
    res = client.post("/api/auditor/analyze-password", json={"password": "WeakPassword1"})
    assert res.status_code == 200
    data = res.json()
    assert "entropy_bits" in data
    assert "strength" in data
    assert "crack_time_estimates" in data


def test_api_generate_password():
    res = client.post("/api/auditor/generate-password", json={"length": 18})
    assert res.status_code == 200
    data = res.json()
    assert "password" in data
    assert len(data["password"]) == 18
    assert data["analysis"]["strength"] in ("Strong", "Very Strong")


def test_api_simulate_search_space():
    res = client.post("/api/auditor/simulate-search-space", json={"charset_type": "alphanumeric", "length": 10, "attempts_per_sec": 5000})
    assert res.status_code == 200
    data = res.json()
    assert data["pool_size"] == 62
    assert "time_to_exhaust_worst_case" in data


def test_api_analyze_wordlist_text():
    res = client.post("/api/auditor/analyze-wordlist-text", json={"text": "pwd1\npwd2\npwd1\n12345678"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_entries"] == 4
    assert data["duplicate_count"] == 1

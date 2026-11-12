# Wi-Fi Password Recovery Tool

A dedicated, professional, local web-based application for **Ubuntu Linux** designed with one primary purpose:

> **Select a Wi-Fi network → Analyze the selected network → Attempt legitimate password recovery → Display the recovered password if genuinely available.**

---

## 1. Product Vision & Workflow

The application focuses strictly on target-specific wireless security analysis and legitimate credential recovery:

```
[ Nearby Wi-Fi Scan ]
        │
        ▼
[ Select Target SSID ] ──> (Optional: Attach router backup file .bin / .conf / .xml)
        │
        ▼
[ TRACE PASSWORD ]
        │
        ├─► Stage 1: Identifying target network (SSID, BSSID, vendor OUI, channel, frequency)
        ├─► Stage 2: Analyzing wireless security (WPA2/WPA3 protocols, ciphers, PMK derivation)
        ├─► Stage 3: Evaluating available recovery evidence (Local profiles, backups, permissions)
        ├─► Stage 4: Running authorized recovery checks (NetworkManager, system keyfiles, backup files)
        ├─► Stage 5: Evaluating recovery feasibility (WPA2 key format compliance)
        └─► Stage 6: Preparing result
                │
                ├── [SUCCESS]: Display recovered password, recovery source, copy button
                └── [NOT RECOVERED]: Honest explanation of technical limits, checks run & next options
```

---

## 2. Recovery Engine & Legitimate Sources

The modular recovery engine distinguishes honestly between:
- `PASSWORD_RECOVERED`: Pre-shared key legitimately recovered from an authorized source.
- `EVIDENCE_INSUFFICIENT`: Candidate data found but does not meet standard WPA key requirements.
- `NO_CREDENTIAL_AVAILABLE`: No pre-shared key stored in local system stores.
- `ADDITIONAL_INPUT_REQUIRED`: User backup file required or provided file did not match.
- `RECOVERY_INFEASIBLE`: Pre-shared key cannot technically be recovered with available evidence.

### Authorized Sources Audited:
1. **Local NetworkManager Connection Profiles:** Queries connection profiles saved on this machine via `nmcli`.
2. **System Connection Keyfiles:** Inspected in `/etc/NetworkManager/system-connections/` if permissions permit.
3. **User-Provided Router Configuration Backups:** Parses `.bin`, `.conf`, `.xml`, `.txt`, `.cfg` exports uploaded by the user to extract pre-shared keys offline.

### Cryptographic Limitations & Ethical Boundaries:
- **No Password Cracking:** Does **not** perform dictionary or brute-force attacks against live networks.
- **No Packet Sniffing / Handshake Attacks:** Under the IEEE 802.11i specification, beacon frames never broadcast pre-shared keys. The 4-way handshake verifies key knowledge without transmitting the plaintext key.
- **Localhost Binding:** Binds strictly to `127.0.0.1` by default.
- **Zero External Telemetry:** All processing, parsing, and recovery runs locally on your machine. Passwords and configuration files are never transmitted to external servers.

---

## 3. Technology Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, WebSockets.
- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite, Lucide Icons.
- **Testing:** Pytest, pytest-asyncio, FastAPI TestClient.

---

## 4. Quick Start

### 1. Prerequisites (Ubuntu Linux)
```bash
sudo apt-get update
sudo apt-get install -y network-manager wireless-tools python3-venv
```

### 2. Start Application
Run the automated launcher:
```bash
./start_dashboard.sh
```
Or start manually:
```bash
# Backend (serves API and built SPA)
source .venv/bin/activate
PYTHONPATH=. uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open your browser at **`http://127.0.0.1:8000`**.

---

## 5. Running Automated Tests

Run the complete test suite (57 tests):
```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

Build the frontend distribution:
```bash
cd frontend
npm run build
```

---

## 6. Project Structure

```
check-wifi/
├── backend/
│   ├── main.py                     # FastAPI application entry & SPA routing
│   ├── api/
│   │   ├── recovery_tool.py        # Core Wi-Fi recovery & network scan API
│   │   ├── auditor.py              # Password security auditor API
│   │   └── wifi.py                 # Wi-Fi endpoints
│   └── services/
│       ├── wifi_scanner.py         # 802.11 scanner & nmcli telemetry parser
│       ├── security_analyzer.py    # Target WPA protocol & cipher analyzer
│       ├── credential_recovery.py  # Local profiles & router backup extractor
│       ├── recovery_engine.py      # 6-stage target recovery pipeline
│       └── websocket_service.py    # Real-time WebSocket event streaming
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── WifiRecoveryMainPage.tsx  # Primary Wi-Fi Password Recovery Screen
│   │   │   ├── CredentialRecoveryPage.tsx # Backup File Analyzer
│   │   │   ├── SecurityAuditorPage.tsx    # Password Security Auditor
│   │   │   └── SettingsPage.tsx           # Settings & Policy
│   │   ├── components/             # Sidebar, Header, etc.
│   │   └── services/api.ts         # Typed API client
│   └── dist/                       # Production SPA assets
└── tests/
    ├── test_wifi_recovery.py       # Core recovery engine & scanning unit tests
    ├── test_decision_engine.py     # Decision logic tests
    ├── test_diagnosis_service.py   # Pipeline tests
    └── test_auditor.py             # Security auditor tests
```

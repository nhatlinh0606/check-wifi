# TP-Link Router Discovery & Recovery Toolkit (Web Dashboard & CLI)

A comprehensive local network administration, discovery, and credential recovery dashboard and CLI toolkit for **Ubuntu Linux**.
Built for network administrators and owners to locate, inspect, and recover access to TP-Link routers on their local area networks safely and non-destructively.

---

## 1. Key Features

- **Local Web Dashboard (FastAPI + React + TypeScript + Tailwind CSS):**
  - **Overview Dashboard:** Live telemetry, active interface, default gateway, connected host counters, candidate router cards.
  - **Network Interfaces:** Interface details, MTU, IPv4 address, subnet mask, CIDR, and default route selector.
  - **Wi-Fi Discovery:** Passive scan of nearby wireless access points (SSID, BSSID, Signal meter, Channel, Security, Band, Vendor OUI) using normal operating system Wi-Fi APIs (`nmcli`).
  - **Router Discovery:** Asynchronous background LAN sweep, live WebSocket streaming progress (`ws://127.0.0.1:8000/ws/scan`), real-time host cards, and deep inspection modal.
  - **Credential Recovery Assistant:** Legitimate manufacturer workflows for Cases A through E, including **Indoor PoE Injector Remote Reset procedures for pole-mounted/outdoor devices** and model-specific hardware reset timing.
  - **Scan History:** Archives discovery sessions into structured JSON reports with an integrated JSON viewer and download options.
- **Standalone CLI Toolkit:**
  - `python3 router_tool.py discover`: Full subnet discovery, port scanning & router identification.
  - `python3 router_tool.py scan`: Quick subnet host discovery.
  - `python3 router_tool.py identify --ip <IP>`: Deep vendor & confidence analysis.
  - `python3 router_tool.py inspect --ip <IP>`: Passive HTTP/HTTPS header and signature examination.
  - `python3 router_tool.py assist --case <A-E>`: Command-line recovery workflows.
  - `python3 router_tool.py report --format json`: Export reports to JSON or TXT.

---

## 2. Security Boundaries & Ethics

This software strictly adheres to authorized administrative and diagnostic guidelines:
- **No Password Cracking:** Does **not** perform brute-force, dictionary attacks, or WPS PIN attacks.
- **No Packet Manipulation:** Does **not** execute deauthentication attacks or WPA/WPA2/WPA3 handshake capturing.
- **No Exploitation:** Does **not** attempt authentication bypass or firmware exploits.
- **Localhost Binding:** Web server binds to `127.0.0.1` by default to prevent exposure to untrusted networks.
- **No Remote Command Injection:** Inputs (IP addresses, interfaces, subnets) are strictly validated.
- **Zero External Telemetry:** All data remains strictly local on your machine.

---

## 3. Project Architecture

```
check-wifi/
├── backend/                        # FastAPI Backend
│   ├── main.py                     # App entry point, CORS, WebSockets, SPA static serving
│   ├── api/
│   │   ├── network.py              # Interface & gateway endpoints
│   │   ├── wifi.py                 # OS Wi-Fi scan & saved profiles
│   │   ├── discovery.py            # Background scan controls & history
│   │   ├── devices.py              # Single-host deep inspection
│   │   └── recovery.py             # Recovery workflows & cases
│   └── services/
│       ├── scan_service.py         # Async background scanner & progress manager
│       ├── wifi_service.py         # nmcli wrapper & Wi-Fi parser
│       ├── websocket_service.py    # Real-time WebSocket event broadcaster
│       └── history_service.py      # JSON report archiving
├── frontend/                       # Modern React Dashboard
│   ├── src/
│   │   ├── components/             # Sidebar, Header, DeviceCard, InspectModal, ProgressBar
│   │   ├── pages/                  # Dashboard, Interfaces, Wifi, Discovery, History, Recovery, Settings
│   │   ├── services/               # Typed API client & WebSocket client
│   │   └── types/                  # TypeScript interface definitions
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── modules/                        # Reusable Python Core Modules
│   ├── network_discovery.py        # Interface detection, routing table, ARP parser
│   ├── arp_scanner.py              # Multi-threaded ping & ARP sweep
│   ├── port_scanner.py             # Non-intrusive TCP handshake checker (80, 443, 8080, etc.)
│   ├── admin_interface.py          # HTTP/HTTPS status, redirects, headers, signatures
│   ├── router_identifier.py        # MAC OUI & confidence scoring engine
│   ├── recovery_assistant.py       # Recovery case database & model guides
│   └── reporter.py                 # Colored terminal & report exporter
├── config/
│   └── vendors.json                # 176 TP-Link OUIs + other vendors (IEEE MA-L)
├── tests/                          # 20 Automated Unit & API Tests
├── reports/                        # Saved JSON telemetry reports
├── Dockerfile                      # Multi-stage production container
├── docker-compose.yml              # Host network mode compose spec
├── router_tool.py                  # Standalone CLI entry point
├── start_dashboard.sh              # Single-command launcher script
└── requirements.txt                # Python dependencies
```

---

## 4. Ubuntu Installation & Setup

### Prerequisites
- Ubuntu 20.04 / 22.04 / 24.04 LTS
- Python 3.10+
- Node.js 18+ and npm (for frontend compilation if developing)
- `iproute2` and `network-manager` (`nmcli`)

### Quick Start (Local Web Dashboard)

```bash
# 1. Clone repository
git clone git@github.com:nhatlinh0606/check-wifi.git
cd check-wifi

# 2. Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Build React frontend (pre-compiled in dist, or build afresh):
cd frontend && npm install && npm run build && cd ..

# 4. Start Dashboard:
./start_dashboard.sh
```

Now open your web browser and navigate to:
**👉 `http://127.0.0.1:8000`**

- Interactive Swagger API docs are accessible at: `http://127.0.0.1:8000/docs`
- Real-time WebSocket stream is at: `ws://127.0.0.1:8000/ws/scan`

---

## 5. Running with Docker Compose

For a containerized setup with host network access (to discover host ARP and network devices):

```bash
docker compose up --build
```
Access the dashboard at `http://127.0.0.1:8000`.

---

## 6. CLI Usage Reference

The original command-line interface remains 100% supported:

```bash
source .venv/bin/activate

# 1. Run full discovery & identification:
python3 router_tool.py discover

# 2. Scan live hosts on specific interface/subnet:
python3 router_tool.py scan --interface wlp0s20f3 --subnet 192.168.1.0/24

# 3. Deeply identify a specific target IP:
python3 router_tool.py identify --ip 192.168.1.1

# 4. Inspect web management portal:
python3 router_tool.py inspect --ip 192.168.1.1

# 5. Access Recovery Assistant guides:
python3 router_tool.py assist --case E

# 6. Export scan report to JSON:
python3 router_tool.py report --format json
```

---

## 7. Recovery Assistant Summary (Cases A - E)

| Scenario | Description | Key Actions |
|---|---|---|
| **Case A** | Reachable Admin Page, Forgot Password | Check model default (`admin/admin` on older models); use web UI "Forgot Password?" verification email; use TP-Link Tether mobile app if previously bound to TP-Link Cloud ID. |
| **Case B** | Known Admin IP, No Credentials | Check HTTP/HTTPS on alternate ports (8080/8443) via Incognito mode; resolve local DNS `http://tplinkwifi.net`. |
| **Case C** | Admin IP Not on Current Subnet | Direct Ethernet connection; renew DHCP (`sudo dhclient`); assign static IP in `192.168.0.x` or `192.168.0.254` (for PharOS/CPE outdoor units). |
| **Case D** | Cannot Connect to Wi-Fi | Connect via wired RJ45 cable to bypass Wi-Fi; inspect locally saved credentials using `nmcli connection show <SSID> -s`. |
| **Case E** | Hardware Factory Reset | **Pole-Mounted / Outdoor Routers (CPE210/510):** Locate the indoor PoE Injector power supply and press the **Remote Reset** button for 10 seconds (no ladder/climbing required). Archer series: hold reset pin for 8-10s; Deco: hold 1s. |

---

## 8. Automated Testing

Run the comprehensive pytest suite covering both core discovery modules and the FastAPI backend:

```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```
**Test Result: 20 passed.**

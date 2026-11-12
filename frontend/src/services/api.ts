import {
  NetworkInterface,
  WifiNetwork,
  DiscoveredDevice,
  ScanStatus,
  ScanHistoryItem,
  RecoveryCase,
  PasswordTraceResult,
  PasswordEvaluation,
  WordlistAnalysisResult,
  SearchSpaceSimulation,
} from '../types';

const API_BASE = '/api';

export async function fetchInterfaces(): Promise<NetworkInterface[]> {
  const res = await fetch(`${API_BASE}/network/interfaces`);
  if (!res.ok) throw new Error('Failed to fetch interfaces');
  return res.json();
}

export async function fetchCurrentInterface(iface?: string): Promise<NetworkInterface> {
  const url = iface
    ? `${API_BASE}/network/current?interface=${encodeURIComponent(iface)}`
    : `${API_BASE}/network/current`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch current interface');
  return res.json();
}

export async function fetchWifiNetworks(rescan = false): Promise<WifiNetwork[]> {
  const res = await fetch(`${API_BASE}/wifi/scan?rescan=${rescan}`);
  if (!res.ok) throw new Error('Failed to fetch Wi-Fi networks');
  return res.json();
}

export async function fetchSavedWifiProfiles(): Promise<Array<{ name: string; uuid: string; type: string; active: boolean }>> {
  const res = await fetch(`${API_BASE}/wifi/saved-profiles`);
  if (!res.ok) throw new Error('Failed to fetch saved Wi-Fi profiles');
  return res.json();
}

export async function traceWifiPassword(ssid: string, bssid?: string): Promise<PasswordTraceResult> {
  const res = await fetch(`${API_BASE}/wifi/trace`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ssid, bssid }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to trace Wi-Fi password');
  }
  return res.json();
}

export async function startDiscoveryScan(iface?: string, subnet?: string): Promise<{ message: string; status: string }> {
  const res = await fetch(`${API_BASE}/discovery/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ interface: iface, subnet: subnet }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to start scan');
  }
  return res.json();
}

export async function stopDiscoveryScan(): Promise<{ message: string; status: string }> {
  const res = await fetch(`${API_BASE}/discovery/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop scan');
  return res.json();
}

export async function fetchScanStatus(): Promise<ScanStatus> {
  const res = await fetch(`${API_BASE}/discovery/status`);
  if (!res.ok) throw new Error('Failed to fetch scan status');
  return res.json();
}

export async function fetchScanHistory(): Promise<ScanHistoryItem[]> {
  const res = await fetch(`${API_BASE}/discovery/history`);
  if (!res.ok) throw new Error('Failed to fetch scan history');
  return res.json();
}

export async function fetchScanReport(reportId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/discovery/history/${encodeURIComponent(reportId)}`);
  if (!res.ok) throw new Error('Failed to fetch scan report');
  return res.json();
}

export async function inspectDevice(ip: string, mac?: string): Promise<DiscoveredDevice> {
  const res = await fetch(`${API_BASE}/devices/inspect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ip, mac }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to inspect device');
  }
  return res.json();
}

export async function fetchRecoveryCases(): Promise<Record<string, RecoveryCase>> {
  const res = await fetch(`${API_BASE}/recovery/cases`);
  if (!res.ok) throw new Error('Failed to fetch recovery cases');
  return res.json();
}

// Security Auditor APIs
export async function analyzePassword(password: string): Promise<PasswordEvaluation> {
  const res = await fetch(`${API_BASE}/auditor/analyze-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) throw new Error('Failed to analyze password');
  return res.json();
}

export async function generatePassword(params: {
  length: number;
  include_upper: boolean;
  include_lower: boolean;
  include_digits: boolean;
  include_symbols: boolean;
  exclude_ambiguous: boolean;
}): Promise<{ password: string; analysis: PasswordEvaluation }> {
  const res = await fetch(`${API_BASE}/auditor/generate-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to generate password');
  return res.json();
}

export async function analyzeWordlistText(text: string): Promise<WordlistAnalysisResult> {
  const res = await fetch(`${API_BASE}/auditor/analyze-wordlist-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to analyze wordlist');
  return res.json();
}

export async function analyzeWordlistFile(file: File): Promise<WordlistAnalysisResult> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/auditor/analyze-wordlist`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload and analyze wordlist');
  }
  return res.json();
}

export async function simulateSearchSpace(params: {
  charset_type: string;
  length: number;
  custom_pool_size?: number;
  attempts_per_sec: number;
}): Promise<SearchSpaceSimulation> {
  const res = await fetch(`${API_BASE}/auditor/simulate-search-space`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to simulate search space');
  return res.json();
}

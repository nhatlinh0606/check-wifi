export interface NetworkInterface {
  name: string;
  ip: string;
  netmask: string;
  cidr: string;
  network: string;
  mac: string;
  is_up: boolean;
  is_default: boolean;
  gateway?: string | null;
}

export interface WifiNetwork {
  ssid: string;
  bssid: string;
  channel: number;
  signal: number;
  bars: string;
  security: string;
  band: string;
  vendor: string;
  is_tplink: boolean;
}

export interface PasswordTraceResult {
  found: boolean;
  ssid: string;
  bssid?: string | null;
  password?: string | null;
  profile_name?: string | null;
  source?: string | null;
  security_type?: string | null;
  message: string;
  explanation?: string | null;
}

export interface EndpointDetail {
  url: string;
  port: number;
  protocol: string;
  status_code: number;
  title?: string | null;
  server_header?: string | null;
  redirect_chain: string[];
  final_url?: string | null;
  auth_realm?: string | null;
  tplink_signatures_found: string[];
  model_hint?: string | null;
}

export interface DiscoveredDevice {
  ip: string;
  mac?: string | null;
  is_gateway: boolean;
  detected_vendor: string;
  is_tplink_candidate: boolean;
  confidence: 'High' | 'Medium' | 'Low' | 'None';
  confidence_score: number;
  evidence: string[];
  model_hint?: string | null;
  admin_url?: string | null;
  open_ports: number[];
  details?: {
    endpoints?: EndpointDetail[];
    port_results?: Array<{ port: number; service: string; is_open: boolean; latency_ms?: number }>;
  };
}

export interface ScanStatus {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step: string;
  interface_info?: NetworkInterface | null;
  discovered_devices: DiscoveredDevice[];
  devices_count: number;
  tplink_count: number;
  last_report_file?: string | null;
  error_message?: string | null;
}

export interface ScanHistoryItem {
  id: string;
  filename: string;
  timestamp: string;
  interface?: string | null;
  subnet?: string | null;
  gateway?: string | null;
  results_count: number;
  tplink_count: number;
}

export interface RecoveryCase {
  title: string;
  summary: string;
  steps: string[];
}

export type PageId =
  | 'wifi-recovery'
  | 'dashboard'
  | 'interfaces'
  | 'wifi'
  | 'discovery'
  | 'history'
  | 'recovery'
  | 'settings';

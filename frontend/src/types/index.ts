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

export interface PasswordEvaluation {
  password_masked: string;
  length: number;
  entropy_bits: number;
  strength: 'Very Weak' | 'Weak' | 'Fair' | 'Strong' | 'Very Strong';
  color: string;
  character_sets: {
    lowercase: boolean;
    uppercase: boolean;
    digits: boolean;
    symbols: boolean;
  };
  warnings: string[];
  recommendations: string[];
  theoretical_combinations: string;
  crack_time_estimates: {
    online_router_5_per_sec: string;
    offline_cpu_10k_per_sec: string;
    offline_gpu_1m_per_sec: string;
  };
}

export interface WordlistAnalysisResult {
  total_entries: number;
  unique_entries: number;
  duplicate_count: number;
  duplicate_rate_pct: number;
  avg_length: number;
  min_length: number;
  max_length: number;
  pure_numeric_count: number;
  pure_numeric_pct: number;
  sequential_count: number;
  sample_weak_entries: Array<{ entry: string; reason: string }>;
  quality_grade: string;
}

export interface SearchSpaceSimulation {
  charset_label: string;
  pool_size: number;
  length: number;
  attempts_per_sec: number;
  total_combinations_scientific: string;
  total_combinations_exact: string;
  time_to_exhaust_worst_case: string;
  time_to_exhaust_average_50pct: string;
  sample_patterns: string[];
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
  | 'auditor'
  | 'dashboard'
  | 'interfaces'
  | 'wifi'
  | 'discovery'
  | 'history'
  | 'recovery'
  | 'settings';

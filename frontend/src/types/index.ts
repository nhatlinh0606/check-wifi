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

export interface HardwareController {
  interface: string;
  driver: string;
  chipset_pci_id: string;
}

export interface WifiNetwork {
  ssid: string;
  bssid: string;
  channel: number;
  frequency?: string;
  band: string;
  signal: number;
  bars: string;
  security: string;
  encryption?: string;
  vendor: string;
  is_connected?: boolean;
  is_tplink: boolean;
}

export interface StageItem {
  id: number;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  details?: any;
}

export interface EapolPacketInfo {
  frame_index: number;
  timestamp: number;
  src_mac: string;
  dst_mac: string;
  bssid?: string | null;
  message_type: string;
  message_description: string;
  key_descriptor_type: number;
  key_descriptor_version: number;
  key_replay_counter: number;
  key_nonce_hex: string;
  key_mic_hex: string;
  key_data_length: number;
  key_data_preview: string;
  is_pairwise: boolean;
  is_ack: boolean;
  has_mic: boolean;
  is_install: boolean;
  is_secure: boolean;
}

export interface HandshakeEvidence {
  conversation_id: string;
  ap_mac: string;
  sta_mac: string;
  associated_ssid?: string | null;
  messages_found: string[];
  completeness: 'COMPLETE_4WAY' | 'VALID_HANDSHAKE_PAIR' | 'INCOMPLETE_HANDSHAKE' | 'NO_HANDSHAKE';
  is_usable_for_offline_validation: boolean;
  anonce_hex?: string | null;
  snonce_hex?: string | null;
  key_mic_hex?: string | null;
  mic_algorithm: string;
  key_replay_counter?: number | null;
  cryptographic_summary: string;
  packet_indices: number[];
}

export interface PcapAnalysisResult {
  status: string;
  filename: string;
  error?: string;
  total_packets: number;
  eapol_packets_count: number;
  beacons_discovered: Array<{ bssid: string; ssid: string }>;
  eapol_frames: EapolPacketInfo[];
  handshake_conversations: HandshakeEvidence[];
  best_handshake?: HandshakeEvidence | null;
  has_valid_handshake: boolean;
}

export interface RecoveryResult {
  status: 'SUCCESS' | 'HANDSHAKE_CAPTURED' | 'NOT_RECOVERED';
  outcome_code:
    | 'PASSWORD_RECOVERED'
    | 'HANDSHAKE_EVIDENCE_AVAILABLE'
    | 'HANDSHAKE_EVIDENCE_INCOMPLETE'
    | 'EVIDENCE_INSUFFICIENT'
    | 'NO_CREDENTIAL_AVAILABLE'
    | 'ADDITIONAL_INPUT_REQUIRED'
    | 'RECOVERY_INFEASIBLE';
  target_ssid: string;
  target_bssid?: string | null;
  recovered_password?: string | null;
  recovery_source?: string | null;
  timestamp: string;
  stages: StageItem[];
  security_analysis: {
    target_ssid: string;
    target_bssid?: string | null;
    protocol_name: string;
    akm_suite: string;
    pairwise_cipher: string;
    pmk_derivation: string;
    frequency_band: string;
    channel: number;
    security_level: string;
    passive_airwave_extraction_possible: boolean;
    technical_limitation_explanation: string;
    interface_telemetry?: any;
  };
  checks_performed: Array<{
    source_id?: string;
    source_name?: string;
    source?: string;
    status: string;
    details?: string;
    description?: string;
    evidence_found?: boolean;
    target_matched?: boolean;
  }>;
  failure_reason?: string | null;
  missing_evidence?: string | null;
  next_legitimate_options: string[];
  technical_limitation_notice: string;
  handshake_evidence?: HandshakeEvidence | null;
  pcap_analysis?: PcapAnalysisResult | null;
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

export interface CredentialSourceAudit {
  source_name: string;
  source_type: string;
  status: 'Checked' | 'Found' | 'Not found' | 'Permission required' | 'Unsupported';
  description: string;
  credentials: Array<{
    ssid?: string;
    bssid?: string;
    identity?: string;
    secret?: string;
    location: string;
    encryption_type?: string;
  }>;
  technical_limitation_note?: string | null;
  matching_credential_found: boolean;
}

export interface RecoveryPlan {
  scenario_id: 'scenario_1' | 'scenario_2' | 'scenario_3' | 'scenario_4' | 'scenario_5';
  scenario_title: string;
  scenario_summary: string;
  confidence_rating: 'High' | 'Medium' | 'Low';
  confirmed_facts: string[];
  working_hypotheses: string[];
  unknown_variables: string[];
  action_steps: Array<{
    step: number;
    title: string;
    instruction: string;
    command?: string;
    caution?: string;
  }>;
  technical_notes: string[];
  model_specific_reset?: {
    model: string;
    hold_duration_sec: number;
    led_indicator: string;
    default_ip: string;
    default_web_url: string;
    default_credentials: string;
  } | null;
  poe_remote_reset_guide?: {
    applicable: boolean;
    indoor_unit: string;
    method: string;
    note: string;
  } | null;
  isp_pppoe_warning: string;
  official_vendor_docs: Array<{
    title: string;
    url: string;
  }>;
}

export interface StageProgress {
  id: number;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  details?: any;
}

export interface DiagnosisStatus {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  current_stage: number;
  stage_message: string;
  stages: StageProgress[];
  has_result: boolean;
  error_message?: string | null;
}

export interface FullDiagnosisResult {
  timestamp: string;
  environment: {
    interfaces: NetworkInterface[];
    primary_interface?: NetworkInterface | null;
    hardware_controllers: HardwareController[];
  };
  wireless: {
    networks_count: number;
    networks: WifiNetwork[];
    tplink_aps_detected: WifiNetwork[];
  };
  routing: {
    default_gateway?: string | null;
    gateway_interface?: string | null;
    connection_type: 'wifi' | 'ethernet' | 'none';
    target_subnet: string;
    dns_servers: string[];
  };
  hosts: {
    hosts_count: number;
    hosts: Array<{ ip: string; mac?: string; is_gateway: boolean }>;
  };
  router_identification: {
    gateway_device?: any;
    detected_vendor: string;
    is_tplink_candidate: boolean;
    candidate_devices: DiscoveredDevice[];
  };
  management: {
    gateway_ip?: string | null;
    open_ports: number[];
    management_endpoints: EndpointDetail[];
    is_management_reachable: boolean;
    model_hint?: string | null;
  };
  credentials: {
    sources_checked_count: number;
    sources: CredentialSourceAudit[];
    matching_credential_found: boolean;
  };
  recovery_plan: RecoveryPlan;
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
  id?: string;
  filename: string;
  timestamp: string;
  interface?: string | null;
  subnet?: string | null;
  gateway?: string | null;
  results_count?: number;
  tplink_count?: number;
  file_size?: number;
  scenario_id?: string;
  scenario_title?: string;
  confidence_rating?: string;
  gateway_ip?: string;
}

export interface RecoveryCase {
  title: string;
  summary: string;
  steps: string[];
}

// Security Auditor Types
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

export type PageId =
  | 'dashboard'
  | 'network-discovery'
  | 'router-identification'
  | 'credential-recovery'
  | 'recovery-plan'
  | 'history'
  | 'auditor'
  | 'settings'
  | 'discovery'
  | 'interfaces'
  | 'wifi'
  | 'recovery'
  | 'wifi-recovery';

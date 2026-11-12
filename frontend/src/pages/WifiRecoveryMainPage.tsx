import React, { useState, useEffect } from 'react';
import {
  Wifi,
  Search,
  RefreshCw,
  KeyRound,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Eye,
  EyeOff,
  Upload,
  AlertTriangle,
  Info,
  Radio,
  FileText,
  Clock,
  Loader2,
  Zap,
} from 'lucide-react';
import { WifiNetwork, RecoveryResult, StageItem } from '../types';
import {
  fetchNearbyNetworks,
  traceTargetPassword,
  uploadRecoveryBackupFile,
} from '../services/api';
import { wsClient } from '../services/websocket';

const DEFAULT_STAGES: StageItem[] = [
  { id: 1, name: 'Identifying target network', status: 'pending' },
  { id: 2, name: 'Analyzing wireless security', status: 'pending' },
  { id: 3, name: 'Evaluating available recovery evidence', status: 'pending' },
  { id: 4, name: 'Running authorized recovery checks', status: 'pending' },
  { id: 5, name: 'Evaluating recovery feasibility', status: 'pending' },
  { id: 6, name: 'Preparing result', status: 'pending' },
];

export const WifiRecoveryMainPage: React.FC = () => {
  const [networks, setNetworks] = useState<WifiNetwork[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState<WifiNetwork | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  // Attached backup file state
  const [backupContent, setBackupContent] = useState<string | null>(null);
  const [backupFilename, setBackupFilename] = useState<string | null>(null);
  const [isUploadingBackup, setIsUploadingBackup] = useState(false);

  // Recovery Execution state
  const [isTracing, setIsTracing] = useState(false);
  const [stages, setStages] = useState<StageItem[]>(DEFAULT_STAGES);
  const [stageMessage, setStageMessage] = useState<string>('Select a network and click Trace Password.');
  const [recoveryResult, setRecoveryResult] = useState<RecoveryResult | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [traceError, setTraceError] = useState<string | null>(null);

  // Load networks on mount
  useEffect(() => {
    handleScanNetworks(false);
  }, []);

  // WebSocket progress listener
  useEffect(() => {
    wsClient.connect();
    const unsubscribe = wsClient.subscribe((event, data) => {
      if (event === 'recovery_stage_progress') {
        if (data.stages) setStages(data.stages);
        if (data.stage_message) setStageMessage(data.stage_message);
      } else if (event === 'recovery_complete') {
        setRecoveryResult(data);
        setIsTracing(false);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleScanNetworks = async (rescan: boolean = true) => {
    setIsScanning(true);
    try {
      const list = await fetchNearbyNetworks(rescan);
      setNetworks(list);
      // Auto-select first network or maintain selected if still available
      if (list.length > 0) {
        if (selectedNetwork) {
          const match = list.find(
            (n) => n.bssid === selectedNetwork.bssid || n.ssid === selectedNetwork.ssid
          );
          if (match) setSelectedNetwork(match);
        } else {
          // Preselect connected or strongest network
          const connected = list.find((n) => n.is_connected);
          setSelectedNetwork(connected || list[0]);
        }
      }
    } catch (err) {
      console.error('Scan error:', err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleSelectNetwork = (net: WifiNetwork) => {
    if (isTracing) return;
    setSelectedNetwork(net);
    setRecoveryResult(null);
    setTraceError(null);
    setStages(DEFAULT_STAGES);
    setStageMessage(`Selected target '${net.ssid}'. Click Trace Password to begin.`);
  };

  const handleBackupUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingBackup(true);
    try {
      const res = await uploadRecoveryBackupFile(file);
      setBackupContent(res.content);
      setBackupFilename(res.filename);
    } catch (err: any) {
      alert(err.message || 'Failed to upload backup file');
    } finally {
      setIsUploadingBackup(false);
    }
  };

  const handleTracePassword = async () => {
    if (!selectedNetwork || isTracing) return;

    setIsTracing(true);
    setTraceError(null);
    setRecoveryResult(null);
    setShowPassword(false);
    setStages(DEFAULT_STAGES.map((s) => ({ ...s, status: 'pending' })));
    setStageMessage('Starting target-specific analysis...');

    try {
      const result = await traceTargetPassword({
        ssid: selectedNetwork.ssid,
        bssid: selectedNetwork.bssid,
        backup_content: backupContent || undefined,
        backup_filename: backupFilename || undefined,
      });
      setRecoveryResult(result);
      if (result.stages) setStages(result.stages);
    } catch (err: any) {
      setTraceError(err.message || 'Trace failed');
    } finally {
      setIsTracing(false);
    }
  };

  const handleCopyPassword = (pwd: string) => {
    navigator.clipboard.writeText(pwd);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2500);
  };

  const filteredNetworks = networks.filter((n) => {
    const q = searchFilter.toLowerCase();
    return (
      n.ssid.toLowerCase().includes(q) ||
      n.bssid.toLowerCase().includes(q) ||
      n.security.toLowerCase().includes(q) ||
      n.vendor.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Banner: Single Purpose Focus */}
      <div className="relative overflow-hidden rounded-2xl border border-blue-500/30 bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 p-5 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold">
              <KeyRound className="w-3.5 h-3.5" />
              Primary Purpose: Legitimate Wi-Fi Credential Recovery
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              Select Wi-Fi Network & Trace Saved Password
            </h1>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Select a target wireless network to analyze its 802.11 security architecture and recover legitimate credentials
              from local system profiles or user-supplied configuration archives. No brute-force or authentication bypass.
            </p>
          </div>

          <button
            onClick={() => handleScanNetworks(true)}
            disabled={isScanning || isTracing}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md shadow-blue-600/30 transition-all cursor-pointer disabled:opacity-50 self-start md:self-auto shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
            {isScanning ? 'Scanning Airwaves...' : 'Scan Wi-Fi Networks'}
          </button>
        </div>
      </div>

      {/* Main Two-Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* =================================================================== */}
        {/* LEFT PANEL: Discovered Wi-Fi Networks (lg:col-span-5) */}
        {/* =================================================================== */}
        <div className="lg:col-span-5 bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Wifi className="w-4 h-4 text-blue-400" />
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                Nearby Networks
              </h2>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {filteredNetworks.length} visible
            </span>
          </div>

          {/* Search Filter */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by SSID, BSSID, or Vendor..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Network Items List */}
          <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
            {isScanning && networks.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                <span>Scanning 802.11 airwaves...</span>
              </div>
            ) : filteredNetworks.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No networks found matching &quot;{searchFilter}&quot;.
              </div>
            ) : (
              filteredNetworks.map((net) => {
                const isSelected = selectedNetwork?.bssid === net.bssid;

                return (
                  <div
                    key={net.bssid}
                    onClick={() => handleSelectNetwork(net)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer select-none ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500/10 shadow-md shadow-blue-500/10'
                        : 'border-slate-800 bg-slate-950/60 hover:bg-slate-800/40 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 truncate">
                        <Radio
                          className={`w-3.5 h-3.5 shrink-0 ${
                            isSelected ? 'text-blue-400' : 'text-slate-500'
                          }`}
                        />
                        <span className="text-xs font-bold text-white truncate">
                          {net.ssid}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        {net.is_connected && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            Connected
                          </span>
                        )}
                        <span className="font-mono text-xs text-slate-300 font-semibold">
                          {net.signal}%
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono mt-2">
                      <span>{net.bssid}</span>
                      <span>Ch {net.channel} ({net.band})</span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] pt-2 mt-2 border-t border-slate-800/60">
                      <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono text-[10px]">
                        {net.security}
                      </span>
                      <span className="text-slate-500 truncate max-w-[150px] text-[10px]">
                        {net.vendor}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* =================================================================== */}
        {/* RIGHT PANEL: Target Analysis & Password Recovery (lg:col-span-7) */}
        {/* =================================================================== */}
        <div className="lg:col-span-7 space-y-5">
          {selectedNetwork ? (
            <>
              {/* Selected Target Profile Card */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-blue-400 tracking-wider">
                      Selected Target Wi-Fi
                    </span>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Wifi className="w-4 h-4 text-blue-400" />
                      {selectedNetwork.ssid}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-xs font-mono">
                      {selectedNetwork.security}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-xs font-mono font-semibold">
                      Signal: {selectedNetwork.signal}%
                    </span>
                  </div>
                </div>

                {/* Target Attributes Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">BSSID (MAC)</span>
                    <div className="font-mono text-slate-200 mt-0.5 truncate">{selectedNetwork.bssid}</div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Channel & Band</span>
                    <div className="font-mono text-slate-200 mt-0.5">
                      Ch {selectedNetwork.channel} • {selectedNetwork.band}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Cipher Suite</span>
                    <div className="font-mono text-slate-200 mt-0.5">{selectedNetwork.encryption || 'AES-CCMP'}</div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Vendor</span>
                    <div className="text-slate-200 mt-0.5 truncate">{selectedNetwork.vendor}</div>
                  </div>
                </div>

                {/* Optional Attached Router Backup */}
                <div className="pt-2 border-t border-slate-800/80">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">
                      Optional: Attach Router Configuration Backup (.bin, .conf, .xml)
                    </span>
                    <label className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors border border-slate-700">
                      <Upload className="w-3 h-3 text-blue-400" />
                      {backupFilename ? 'Replace Backup' : 'Attach File'}
                      <input
                        type="file"
                        onChange={handleBackupUpload}
                        accept=".bin,.conf,.xml,.txt,.cfg,.tar.gz"
                        disabled={isUploadingBackup || isTracing}
                        className="hidden"
                      />
                    </label>
                  </div>
                  {backupFilename && (
                    <div className="mt-2 p-2 rounded bg-slate-950 border border-blue-500/30 flex items-center justify-between text-xs text-blue-300">
                      <span className="flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        Attached: {backupFilename}
                      </span>
                      <button
                        onClick={() => {
                          setBackupFilename(null);
                          setBackupContent(null);
                        }}
                        className="text-[10px] text-slate-400 hover:text-rose-400"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>

                {/* Prominent Action Button: TRACE PASSWORD */}
                <div className="pt-2">
                  <button
                    onClick={handleTracePassword}
                    disabled={isTracing}
                    className="w-full flex items-center justify-center gap-2.5 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-600/30 hover:scale-[1.01] active:scale-[0.99] transition-all cursor-pointer disabled:opacity-50"
                  >
                    {isTracing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Tracing Password for &quot;{selectedNetwork.ssid}&quot;...
                      </>
                    ) : (
                      <>
                        <KeyRound className="w-4 h-4" />
                        TRACE PASSWORD
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Real-Time 6-Stage Progress Card */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5 text-blue-400" />
                    Target Analysis Stages (6 Steps)
                  </h4>
                  <span className="text-xs text-slate-400 font-mono">
                    {stageMessage}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {stages.map((stg) => {
                    const isDone = stg.status === 'completed';
                    const isActive = stg.status === 'active';
                    const isFailed = stg.status === 'failed';

                    return (
                      <div
                        key={stg.id}
                        className={`p-2.5 rounded-xl border flex items-center justify-between transition-all ${
                          isActive
                            ? 'border-blue-500 bg-blue-500/10'
                            : isDone
                            ? 'border-emerald-500/30 bg-emerald-500/5'
                            : isFailed
                            ? 'border-rose-500/30 bg-rose-500/5'
                            : 'border-slate-800/80 bg-slate-950/40 text-slate-500'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-4 h-4 rounded-full flex items-center justify-center font-mono text-[10px] font-bold ${
                              isActive
                                ? 'bg-blue-600 text-white'
                                : isDone
                                ? 'bg-emerald-600 text-white'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {stg.id}
                          </span>
                          <span className={`font-semibold ${isActive ? 'text-white' : isDone ? 'text-slate-200' : 'text-slate-400'}`}>
                            {stg.name}
                          </span>
                        </div>

                        {isActive && <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />}
                        {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                        {isFailed && <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                        {!isActive && !isDone && !isFailed && <Clock className="w-3.5 h-3.5 text-slate-600" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Error Alert */}
              {traceError && (
                <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{traceError}</span>
                </div>
              )}

              {/* ============================================================= */}
              {/* RESULT SCREEN: SUCCESS or NOT RECOVERED */}
              {/* ============================================================= */}
              {recoveryResult && (
                <div className="animate-in fade-in duration-300">
                  {recoveryResult.status === 'SUCCESS' ? (
                    /* SUCCESS STATE */
                    <div className="bg-slate-900/90 border border-emerald-500/50 rounded-2xl p-6 shadow-2xl space-y-4">
                      <div className="flex items-center justify-between border-b border-emerald-500/30 pb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                            <CheckCircle2 className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="text-xs uppercase font-bold text-emerald-400 tracking-wider">
                              Password Genuinely Recovered
                            </div>
                            <div className="text-sm font-bold text-white">
                              {recoveryResult.target_ssid}
                            </div>
                          </div>
                        </div>

                        <span className="text-[11px] font-mono text-slate-400">
                          {new Date(recoveryResult.timestamp).toLocaleTimeString()}
                        </span>
                      </div>

                      {/* Password Display Box */}
                      <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-2">
                        <div className="flex items-center justify-between text-xs text-slate-400">
                          <span>Recovered Pre-Shared Key (PSK):</span>
                          <span className="font-mono text-emerald-400">
                            Source: {recoveryResult.recovery_source}
                          </span>
                        </div>

                        <div className="flex items-center justify-between gap-3 pt-1">
                          <div className="font-mono text-xl font-extrabold text-emerald-300 tracking-wider select-all">
                            {showPassword ? recoveryResult.recovered_password : '••••••••••••••••'}
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setShowPassword(!showPassword)}
                              className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition-colors cursor-pointer"
                              title={showPassword ? 'Hide Password' : 'Show Password'}
                            >
                              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>

                            <button
                              onClick={() => handleCopyPassword(recoveryResult.recovered_password || '')}
                              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs transition-all shadow-md shadow-emerald-600/30 cursor-pointer"
                            >
                              {isCopied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                              {isCopied ? 'Copied!' : 'Copy Password'}
                            </button>
                          </div>
                        </div>
                      </div>

                      <div className="text-xs text-slate-300 space-y-1">
                        <span className="font-semibold text-white">Target Verification: </span>
                        <span>SSID: {recoveryResult.target_ssid} • BSSID: {recoveryResult.target_bssid || 'Matched'}</span>
                      </div>
                    </div>
                  ) : (
                    /* NOT RECOVERED STATE */
                    <div className="bg-slate-900/90 border border-rose-500/40 rounded-2xl p-6 shadow-2xl space-y-5">
                      <div className="flex items-center justify-between border-b border-rose-500/20 pb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
                            <XCircle className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="text-xs uppercase font-bold text-rose-400 tracking-wider">
                              Password Not Recovered
                            </div>
                            <div className="text-sm font-bold text-white">
                              {recoveryResult.target_ssid}
                            </div>
                          </div>
                        </div>

                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-xs font-mono">
                          {recoveryResult.outcome_code}
                        </span>
                      </div>

                      {/* Technical Limitation Notice */}
                      <div className="p-3.5 rounded-xl bg-slate-950/80 border border-blue-500/30 text-xs text-slate-300 space-y-1">
                        <div className="font-bold text-blue-300 flex items-center gap-1.5">
                          <Info className="w-3.5 h-3.5" />
                          Cryptographic Limitation of Passive Wi-Fi Scanning:
                        </div>
                        <p className="text-slate-400 leading-relaxed text-[11px]">
                          {recoveryResult.technical_limitation_notice}
                        </p>
                      </div>

                      {/* What was actually analyzed */}
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-white uppercase tracking-wider">
                          Actual Checks Performed:
                        </div>
                        <div className="divide-y divide-slate-800 rounded-xl bg-slate-950/60 border border-slate-800 overflow-hidden text-xs">
                          {recoveryResult.checks_performed.map((chk, i) => (
                            <div key={i} className="p-3 flex items-start justify-between gap-3">
                              <div>
                                <span className="font-semibold text-slate-200">{chk.source}:</span>
                                <p className="text-[11px] text-slate-400 mt-0.5">{chk.details}</p>
                              </div>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold shrink-0 ${
                                  chk.status === 'Found'
                                    ? 'bg-emerald-500/20 text-emerald-300'
                                    : 'bg-slate-800 text-slate-400'
                                }`}
                              >
                                {chk.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Missing Evidence Explanation */}
                      {recoveryResult.missing_evidence && (
                        <div className="text-xs text-slate-300 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                          <span className="font-bold text-amber-300">Missing Evidence: </span>
                          <span>{recoveryResult.missing_evidence}</span>
                        </div>
                      )}

                      {/* Next Legitimate Recovery Options */}
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                          Next Legitimate Recovery Options:
                        </div>
                        <ul className="space-y-1.5 text-xs text-slate-300">
                          {recoveryResult.next_legitimate_options.map((opt, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-emerald-400 font-bold">•</span>
                              <span>{opt}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            /* Empty State */
            <div className="p-16 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
              <Wifi className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-white">No Target Network Selected</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Please select a Wi-Fi network from the list on the left to analyze its security protocol
                and attempt authorized password recovery.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

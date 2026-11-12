import React from 'react';
import { RefreshCw, Play, Square, Globe } from 'lucide-react';
import { PageId } from '../types';

interface HeaderProps {
  currentPage: PageId;
  onQuickDiagnosis: () => void;
  onStopDiagnosis: () => void;
  isDiagnosing: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onQuickDiagnosis,
  onStopDiagnosis,
  isDiagnosing,
  onRefresh,
  isRefreshing,
}) => {
  const titles: Partial<Record<PageId, { title: string; subtitle: string }>> = {
    dashboard: {
      title: 'Autonomous Router Discovery & Recovery Assistant',
      subtitle: 'Real-time telemetry, 8-stage autonomous pipeline, and evidence-based recovery plan',
    },
    'network-discovery': {
      title: 'Stage A: Network Discovery & Wireless Topology',
      subtitle: 'Passive 802.11 airwave scan, Linux network controllers, kernel drivers, and routing table',
    },
    'router-identification': {
      title: 'Stage B & C: Router Identification & Management Web Portals',
      subtitle: 'MAC OUI resolution, port scanning, web server headers, auth realms, and direct web links',
    },
    'credential-recovery': {
      title: 'Stage D: Credential Stores Audit & Backup Analysis',
      subtitle: 'Audit legitimate local NetworkManager profiles, keyfiles, and analyze offline router backup files',
    },
    'recovery-plan': {
      title: 'Stage E: Recovery Decision Engine & Step-by-Step Procedure',
      subtitle: 'Deterministic 5-scenario decision matrix, model-specific reset timings, and PoE remote reset guide',
    },
    history: {
      title: 'Scan & Diagnosis History',
      subtitle: 'Historical diagnostic logs and structured JSON telemetry reports',
    },
    auditor: {
      title: 'Password Security Auditor',
      subtitle: 'Entropy evaluation, strong WPA2/WPA3 password generation, wordlist quality audit, and search simulator',
    },
    settings: {
      title: 'Settings & Security Policy',
      subtitle: 'Local server configuration, diagnostic timeout thresholds, and interface bindings',
    },
  };

  const { title, subtitle } = titles[currentPage] || { title: 'Dashboard', subtitle: '' };

  return (
    <header className="h-16 px-8 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-base font-bold text-white flex items-center gap-2">
          {title}
        </h1>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800 cursor-pointer"
          title="Refresh view data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
        </button>

        {isDiagnosing ? (
          <button
            onClick={onStopDiagnosis}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold shadow-md bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30 transition-all cursor-pointer"
          >
            <Square className="w-3.5 h-3.5 fill-white" />
            Stop Diagnosis
          </button>
        ) : (
          <button
            onClick={onQuickDiagnosis}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold shadow-md bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/30 transition-all cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            Start Diagnosis
          </button>
        )}

        <div className="h-6 w-px bg-slate-800 mx-1" />

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
          <Globe className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-mono text-slate-300">127.0.0.1:8000</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
        </div>
      </div>
    </header>
  );
};

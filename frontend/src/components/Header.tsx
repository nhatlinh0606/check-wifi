import React from 'react';
import { RefreshCw, Play, Globe } from 'lucide-react';
import { PageId } from '../types';

interface HeaderProps {
  currentPage: PageId;
  onQuickScan: () => void;
  isScanning: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onQuickScan,
  isScanning,
  onRefresh,
  isRefreshing,
}) => {
  const titles: Record<PageId, { title: string; subtitle: string }> = {
    'wifi-recovery': {
      title: 'Wi-Fi Password Recovery',
      subtitle: 'Select any nearby Wi-Fi network and trace saved passwords from local NetworkManager profiles',
    },
    auditor: {
      title: 'Password Security Auditor',
      subtitle: 'Audit password entropy, generate strong WPA2/WPA3 keys, analyze wordlists, and simulate search spaces',
    },
    dashboard: {
      title: 'Network Overview',
      subtitle: 'Real-time telemetry, interface topology & discovered router candidates',
    },
    interfaces: {
      title: 'Network Interfaces',
      subtitle: 'System network controllers, IP routing, subnet masks and hardware MACs',
    },
    wifi: {
      title: 'Wi-Fi Discovery',
      subtitle: 'Passive operating system wireless scan for nearby SSIDs and router vendors',
    },
    discovery: {
      title: 'Router Discovery & Diagnostics',
      subtitle: 'Active LAN host sweep, TCP service inspection & TP-Link signature matching',
    },
    history: {
      title: 'Scan History',
      subtitle: 'Historical diagnostic logs and structured JSON telemetry reports',
    },
    recovery: {
      title: 'Recovery Assistant',
      subtitle: 'Legitimate credential recovery workflows and model-specific hardware guides',
    },
    settings: {
      title: 'Settings & Security',
      subtitle: 'Local server configuration, diagnostic timeout thresholds and policy',
    },
  };

  const { title, subtitle } = titles[currentPage] || { title: 'Dashboard', subtitle: '' };

  return (
    <header className="h-16 px-8 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-lg font-bold text-white flex items-center gap-2">
          {title}
        </h1>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800"
          title="Refresh view data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
        </button>

        <button
          onClick={onQuickScan}
          disabled={isScanning}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold shadow-md transition-all ${
            isScanning
              ? 'bg-blue-600/50 text-blue-200 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/30'
          }`}
        >
          <Play className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
          {isScanning ? 'Scanning...' : 'Start Discovery'}
        </button>

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

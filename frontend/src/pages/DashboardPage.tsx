import React from 'react';
import {
  Network,
  Router,
  Server,
  Wifi,
  Radio,
  ArrowRight,
  LifeBuoy,
} from 'lucide-react';
import { NetworkInterface, DiscoveredDevice, ScanStatus, PageId } from '../types';
import { DeviceCard } from '../components/DeviceCard';
import { ProgressBar } from '../components/ProgressBar';

interface DashboardPageProps {
  activeInterface: NetworkInterface | null;
  scanStatus: ScanStatus;
  devices: DiscoveredDevice[];
  onStartScan: () => void;
  onCancelScan: () => void;
  onNavigate: (page: PageId) => void;
  onInspectDevice: (device: DiscoveredDevice) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  activeInterface,
  scanStatus,
  devices,
  onStartScan,
  onCancelScan,
  onNavigate,
  onInspectDevice,
}) => {
  const isScanning = scanStatus.status === 'running';
  const tplinkCandidates = devices.filter((d) => d.is_tplink_candidate);

  return (
    <div className="space-y-6">
      {/* Real-time Progress Bar */}
      <ProgressBar
        progress={scanStatus.progress}
        currentStep={scanStatus.current_step}
        isScanning={isScanning}
        onCancel={onCancelScan}
      />

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Interface */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Active Interface</span>
            <Network className="w-4 h-4 text-blue-400" />
          </div>
          <div className="font-mono font-bold text-xl text-white">
            {activeInterface ? activeInterface.name : 'None'}
          </div>
          <div className="text-xs text-slate-400 mt-1 truncate">
            IP: <span className="text-slate-200 font-mono">{activeInterface?.ip || 'N/A'}</span>
          </div>
        </div>

        {/* Default Gateway */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Default Gateway</span>
            <Router className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="font-mono font-bold text-xl text-indigo-300">
            {activeInterface?.gateway || 'Not set'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Subnet: <span className="text-slate-200 font-mono">{activeInterface?.network || 'N/A'}</span>
          </div>
        </div>

        {/* Discovered Hosts */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Connected LAN Hosts</span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="font-mono font-bold text-xl text-white">
            {devices.length}
          </div>
          <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
            Active on current subnet
          </div>
        </div>

        {/* TP-Link Candidates */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">TP-Link Candidates</span>
            <Radio className="w-4 h-4 text-amber-400" />
          </div>
          <div className="font-mono font-bold text-xl text-amber-300">
            {tplinkCandidates.length}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {tplinkCandidates.length > 0 ? 'Identified by OUI / Web' : 'None detected'}
          </div>
        </div>
      </div>

      {/* Quick Action Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-slate-900/60 border border-blue-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            Automated LAN & Router Diagnostics
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Scan your local subnet to discover active hosts, resolve MAC OUI vendors, detect open management ports,
            and inspect web portal headers safely.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => onNavigate('wifi')}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors flex items-center gap-1.5"
          >
            <Wifi className="w-3.5 h-3.5 text-blue-400" />
            Scan Nearby Wi-Fi
          </button>
          <button
            onClick={onStartScan}
            disabled={isScanning}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-lg shadow-blue-600/30 transition-all flex items-center gap-1.5"
          >
            <Radio className="w-3.5 h-3.5" />
            {isScanning ? 'Scanning...' : 'Start Discovery'}
          </button>
        </div>
      </div>

      {/* Discovered Candidates Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white">Discovered Devices & Gateways</h3>
            <p className="text-xs text-slate-400">
              Showing active network endpoints detected in current and recent scans
            </p>
          </div>
          <button
            onClick={() => onNavigate('discovery')}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors"
          >
            View All ({devices.length})
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {devices.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/80">
            <Radio className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-slate-300">No Devices Discovered Yet</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
              Click &quot;Start Discovery&quot; to scan your local network interface for active IP addresses, routers, and open services.
            </p>
            <button
              onClick={onStartScan}
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white inline-flex items-center gap-2"
            >
              <Radio className="w-3.5 h-3.5" />
              Start First Scan
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {devices.slice(0, 4).map((device) => (
              <DeviceCard
                key={device.ip}
                device={device}
                onInspect={onInspectDevice}
              />
            ))}
          </div>
        )}
      </div>

      {/* Recovery Assistant Callout */}
      <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <LifeBuoy className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Lost router management password?</div>
            <div className="text-xs text-slate-400">
              Check model-specific factory reset procedures, Tether app recovery, or PoE Remote Reset.
            </div>
          </div>
        </div>
        <button
          onClick={() => onNavigate('recovery')}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition-colors shrink-0"
        >
          Open Assistant
        </button>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  Play,
  RotateCcw,
  Search,
  Grid,
  List as ListIcon,
  Radio,
} from 'lucide-react';
import { NetworkInterface, DiscoveredDevice, ScanStatus } from '../types';
import { DeviceCard } from '../components/DeviceCard';
import { ProgressBar } from '../components/ProgressBar';

interface RouterDiscoveryPageProps {
  interfaces: NetworkInterface[];
  selectedInterface: string | null;
  onSelectInterface: (iface: string) => void;
  scanStatus: ScanStatus;
  devices: DiscoveredDevice[];
  onStartScan: (iface?: string, subnet?: string) => void;
  onCancelScan: () => void;
  onInspectDevice: (device: DiscoveredDevice) => void;
}

export const RouterDiscoveryPage: React.FC<RouterDiscoveryPageProps> = ({
  interfaces,
  selectedInterface,
  onSelectInterface,
  scanStatus,
  devices,
  onStartScan,
  onCancelScan,
  onInspectDevice,
}) => {
  const [customSubnet, setCustomSubnet] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'tplink' | 'gateway'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [searchTerm, setSearchTerm] = useState('');

  const isScanning = scanStatus.status === 'running';

  const currentIface = interfaces.find((i) => i.name === selectedInterface) || interfaces[0];

  const handleStart = () => {
    onStartScan(selectedInterface || undefined, customSubnet || undefined);
  };

  const filteredDevices = devices.filter((d) => {
    const matchesSearch =
      d.ip.includes(searchTerm) ||
      (d.mac && d.mac.toLowerCase().includes(searchTerm.toLowerCase())) ||
      d.detected_vendor.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch) return false;

    if (filterMode === 'tplink') return d.is_tplink_candidate;
    if (filterMode === 'gateway') return d.is_gateway;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Configuration & Trigger Card */}
      <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Radio className="w-5 h-5 text-blue-400" />
              Router & Device Discovery Workbench
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select network parameters to perform an asynchronous ARP & TCP service sweep
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isScanning ? (
              <button
                onClick={onCancelScan}
                className="px-4 py-2 rounded-xl bg-red-600/30 hover:bg-red-600 text-red-200 hover:text-white border border-red-500/40 text-xs font-semibold flex items-center gap-2 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Cancel Scan
              </button>
            ) : (
              <button
                onClick={handleStart}
                className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 flex items-center gap-2 transition-all"
              >
                <Play className="w-4 h-4 fill-current" />
                Start Subnet Discovery
              </button>
            )}
          </div>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2 border-t border-slate-800">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Network Interface
            </label>
            <select
              value={selectedInterface || ''}
              onChange={(e) => onSelectInterface(e.target.value)}
              disabled={isScanning}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            >
              {interfaces.map((i) => (
                <option key={i.name} value={i.name}>
                  {i.name} ({i.ip}) {i.is_default ? '★ Default Route' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Target Subnet CIDR (Leave empty for default)
            </label>
            <input
              type="text"
              placeholder={currentIface ? currentIface.network : '192.168.1.0/24'}
              value={customSubnet}
              onChange={(e) => setCustomSubnet(e.target.value)}
              disabled={isScanning}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex flex-col justify-end">
            <div className="text-[11px] text-slate-400 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              Gateway: <span className="font-mono text-emerald-400 font-bold">{currentIface?.gateway || 'N/A'}</span>
              <span className="mx-2">•</span>
              Subnet: <span className="font-mono text-slate-200">{customSubnet || currentIface?.network || 'Auto'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Progress Bar */}
      <ProgressBar
        progress={scanStatus.progress}
        currentStep={scanStatus.current_step}
        isScanning={isScanning}
        onCancel={onCancelScan}
      />

      {/* Filter and View Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter IP or MAC..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex rounded-lg bg-slate-950 p-0.5 border border-slate-800">
            <button
              onClick={() => setFilterMode('all')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterMode === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All ({devices.length})
            </button>
            <button
              onClick={() => setFilterMode('tplink')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterMode === 'tplink' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              TP-Link ({devices.filter((d) => d.is_tplink_candidate).length})
            </button>
            <button
              onClick={() => setFilterMode('gateway')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterMode === 'gateway' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Gateway Only
            </button>
          </div>
        </div>

        <div className="flex items-center gap-1 self-end sm:self-auto">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-lg border transition-colors ${
              viewMode === 'grid'
                ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
                : 'bg-slate-950 text-slate-400 border-slate-800'
            }`}
            title="Grid View"
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`p-1.5 rounded-lg border transition-colors ${
              viewMode === 'table'
                ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
                : 'bg-slate-950 text-slate-400 border-slate-800'
            }`}
            title="Table View"
          >
            <ListIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Discovered Items */}
      {filteredDevices.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
          <Radio className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-300">No matching devices</h4>
          <p className="text-xs text-slate-500 mt-1">
            {isScanning
              ? 'Scan in progress, devices will appear incrementally...'
              : 'Click "Start Subnet Discovery" above to begin scanning.'}
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredDevices.map((device) => (
            <DeviceCard
              key={device.ip}
              device={device}
              onInspect={onInspectDevice}
            />
          ))}
        </div>
      ) : (
        <div className="border border-slate-800 rounded-2xl overflow-hidden bg-slate-900/60 backdrop-blur-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 text-[11px]">
              <tr>
                <th className="py-3 px-4">IP Address</th>
                <th className="py-3 px-4">MAC Address</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Vendor</th>
                <th className="py-3 px-4 text-center">Confidence</th>
                <th className="py-3 px-4">Open Ports</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredDevices.map((d) => (
                <tr key={d.ip} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-white">{d.ip}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{d.mac || 'N/A'}</td>
                  <td className="py-3 px-4">
                    {d.is_gateway ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
                        GATEWAY
                      </span>
                    ) : (
                      <span className="text-slate-500">Host</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-200">{d.detected_vendor}</td>
                  <td className="py-3 px-4 text-center">
                    <span
                      className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                        d.confidence === 'High'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : d.confidence === 'Medium'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'text-slate-500'
                      }`}
                    >
                      {d.confidence} ({d.confidence_score}%)
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">
                    {d.open_ports.join(', ') || '-'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onInspectDevice(d)}
                      className="px-2.5 py-1 rounded bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white transition-colors text-[11px]"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import {
  Wifi,
  Network,
  Cpu,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Radio,
} from 'lucide-react';
import { FullDiagnosisResult, WifiNetwork, NetworkInterface, HardwareController } from '../types';

interface NetworkDiscoveryPageProps {
  latestDiagnosis: FullDiagnosisResult | null;
  onRefreshWifi: () => void;
  isRefreshing: boolean;
}

export const NetworkDiscoveryPage: React.FC<NetworkDiscoveryPageProps> = ({
  latestDiagnosis,
  onRefreshWifi,
  isRefreshing,
}) => {
  const [activeTab, setActiveTab] = useState<'wireless' | 'topology'>('wireless');
  const [searchFilter, setSearchFilter] = useState('');
  const [onlyTplink, setOnlyTplink] = useState(false);

  const wirelessData = latestDiagnosis?.wireless;
  const envData = latestDiagnosis?.environment;
  const routingData = latestDiagnosis?.routing;

  const networks: WifiNetwork[] = wirelessData?.networks || [];
  const interfaces: NetworkInterface[] = envData?.interfaces || [];
  const hwControllers: HardwareController[] = envData?.hardware_controllers || [];

  const filteredNetworks = networks.filter((n) => {
    const matchesSearch =
      n.ssid.toLowerCase().includes(searchFilter.toLowerCase()) ||
      n.bssid.toLowerCase().includes(searchFilter.toLowerCase()) ||
      n.vendor.toLowerCase().includes(searchFilter.toLowerCase());
    const matchesTplink = onlyTplink ? n.is_tplink : true;
    return matchesSearch && matchesTplink;
  });

  return (
    <div className="space-y-6">
      {/* Header Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2 p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab('wireless')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'wireless'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Wifi className="w-3.5 h-3.5" />
            Wireless Airwaves & SSIDs ({networks.length})
          </button>
          <button
            onClick={() => setActiveTab('topology')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'topology'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            Linux Interfaces & Hardware ({interfaces.length})
          </button>
        </div>

        {activeTab === 'wireless' && (
          <div className="flex items-center gap-3">
            <button
              onClick={onRefreshWifi}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
              Rescan Airwaves
            </button>
          </div>
        )}
      </div>

      {/* Stage A Wireless View */}
      {activeTab === 'wireless' && (
        <div className="space-y-5">
          {/* Important Technical Limitation Alert */}
          <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-500/5 flex items-start gap-3 text-xs text-slate-300">
            <AlertCircle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white">Cryptographic Limitation of Passive Wireless Scanning: </span>
              Wi-Fi beacons broadcast in the clear contain network SSID, BSSID, security protocol (WPA2/WPA3), channel, and signal level.
              Pre-shared passwords (PSK) are <strong>never</strong> transmitted in beacon frames.
              If the Wi-Fi password is unknown, connecting an <strong>Ethernet cable</strong> provides immediate direct Layer 2 access without requiring a Wi-Fi password.
            </div>
          </div>

          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by SSID, BSSID, or Vendor..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={onlyTplink}
                onChange={(e) => setOnlyTplink(e.target.checked)}
                className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
              />
              Show TP-Link Candidates Only
            </label>
          </div>

          {/* Wireless Networks Table */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">SSID</th>
                    <th className="py-3 px-4">BSSID (MAC)</th>
                    <th className="py-3 px-4">Signal</th>
                    <th className="py-3 px-4">Channel</th>
                    <th className="py-3 px-4">Band</th>
                    <th className="py-3 px-4">Security</th>
                    <th className="py-3 px-4">Detected Vendor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300 font-normal">
                  {filteredNetworks.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        No wireless networks found matching criteria. Click &quot;Rescan Airwaves&quot; or start an Automatic Diagnosis.
                      </td>
                    </tr>
                  ) : (
                    filteredNetworks.map((net, idx) => (
                      <tr key={`${net.bssid}-${idx}`} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                          <Radio className="w-3.5 h-3.5 text-blue-400" />
                          <span>{net.ssid || '<Hidden SSID>'}</span>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400">{net.bssid}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-slate-200">{net.signal}%</span>
                            <span className="text-[10px] text-slate-500 font-mono">({net.bars})</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono">{net.channel}</td>
                        <td className="py-3 px-4 font-mono">{net.band || '2.4 GHz'}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                            {net.security}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {net.is_tplink ? (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-semibold border border-blue-500/30 text-[11px]">
                              <CheckCircle2 className="w-3 h-3 text-blue-400" />
                              TP-Link
                            </span>
                          ) : (
                            <span className="text-slate-400">{net.vendor || 'Unknown'}</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Stage A Linux Topology View */}
      {activeTab === 'topology' && (
        <div className="space-y-6">
          {/* Active Routing Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="text-xs text-slate-400 font-medium mb-1">Default Gateway Route</div>
              <div className="text-base font-mono font-bold text-emerald-400">
                {routingData?.default_gateway || 'None detected'}
              </div>
              <div className="text-xs text-slate-500 mt-1">Interface: {routingData?.gateway_interface || 'N/A'}</div>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="text-xs text-slate-400 font-medium mb-1">Target LAN Subnet</div>
              <div className="text-base font-mono font-bold text-white">
                {routingData?.target_subnet || '192.168.1.0/24'}
              </div>
              <div className="text-xs text-slate-500 mt-1">Connection Medium: {routingData?.connection_type || 'N/A'}</div>
            </div>

            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="text-xs text-slate-400 font-medium mb-1">Active DNS Servers</div>
              <div className="text-xs font-mono font-bold text-blue-300">
                {routingData?.dns_servers?.length ? routingData.dns_servers.join(', ') : '127.0.0.53 (systemd-resolved)'}
              </div>
              <div className="text-xs text-slate-500 mt-1">Local Resolvers</div>
            </div>
          </div>

          {/* Network Interfaces Table */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Network className="w-4 h-4 text-blue-400" />
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  System Network Interfaces
                </h4>
              </div>
              <span className="text-xs text-slate-500 font-mono">Found {interfaces.length} interface(s)</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Interface</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">IPv4 Address</th>
                    <th className="py-3 px-4">Netmask / CIDR</th>
                    <th className="py-3 px-4">MAC Address</th>
                    <th className="py-3 px-4">Default Route</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {interfaces.map((iface) => (
                    <tr key={iface.name} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-mono font-bold text-white flex items-center gap-2">
                        {iface.name.startsWith('wl') ? (
                          <Wifi className="w-3.5 h-3.5 text-blue-400" />
                        ) : (
                          <Network className="w-3.5 h-3.5 text-emerald-400" />
                        )}
                        <span>{iface.name}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                            iface.is_up ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'
                          }`}
                        >
                          {iface.is_up ? 'UP' : 'DOWN'}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono">{iface.ip || 'No IP assigned'}</td>
                      <td className="py-3 px-4 font-mono">{iface.netmask} ({iface.cidr})</td>
                      <td className="py-3 px-4 font-mono text-slate-400">{iface.mac || 'N/A'}</td>
                      <td className="py-3 px-4">
                        {iface.is_default ? (
                          <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-semibold border border-blue-500/30 text-[11px]">
                            Default Gateway
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Hardware Controllers via Sysfs */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Network Hardware Controllers & Kernel Drivers (sysfs)
              </h4>
            </div>

            <div className="divide-y divide-slate-800/60">
              {hwControllers.map((hw, idx) => (
                <div key={idx} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-800/20">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-white px-2 py-1 rounded bg-slate-800 text-xs">
                      {hw.interface}
                    </span>
                    <div>
                      <div className="text-xs font-semibold text-slate-200">
                        Driver: <span className="text-purple-300 font-mono">{hw.driver}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Hardware PCI / Device ID: {hw.chipset_pci_id}
                      </div>
                    </div>
                  </div>
                  <span className="text-[11px] text-emerald-400 font-mono">Kernel Driver Active</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

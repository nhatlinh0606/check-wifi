import React, { useState } from 'react';
import {
  Wifi,
  RefreshCw,
  Lock,
  Unlock,
  Search,
  ArrowRight,
  Bookmark,
} from 'lucide-react';
import { WifiNetwork, PageId } from '../types';

interface WifiDiscoveryPageProps {
  networks: WifiNetwork[];
  savedProfiles: Array<{ name: string; uuid: string; type: string; active: boolean }>;
  isRefreshing: boolean;
  onRefresh: (rescan: boolean) => void;
  onNavigate: (page: PageId) => void;
}

export const WifiDiscoveryPage: React.FC<WifiDiscoveryPageProps> = ({
  networks,
  savedProfiles,
  isRefreshing,
  onRefresh,
  onNavigate,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTplinkOnly, setFilterTplinkOnly] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState<WifiNetwork | null>(null);

  const filteredNetworks = networks.filter((net) => {
    const matchesSearch =
      net.ssid.toLowerCase().includes(searchTerm.toLowerCase()) ||
      net.bssid.toLowerCase().includes(searchTerm.toLowerCase()) ||
      net.vendor.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTplink = !filterTplinkOnly || net.is_tplink;
    return matchesSearch && matchesTplink;
  });

  const getSignalColor = (signal: number) => {
    if (signal >= 75) return 'text-emerald-400';
    if (signal >= 50) return 'text-blue-400';
    if (signal >= 30) return 'text-amber-400';
    return 'text-rose-400';
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            Nearby Wireless Access Points
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
              {filteredNetworks.length} found
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Detected via standard Linux wireless driver APIs. Strictly passive diagnostic information.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onRefresh(true)}
            disabled={isRefreshing}
            className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-blue-600/30"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Rescanning Airwaves...' : 'Rescan Wi-Fi'}
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search SSID, BSSID or Vendor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
            <input
              type="checkbox"
              checked={filterTplinkOnly}
              onChange={(e) => setFilterTplinkOnly(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
            />
            Show TP-Link APs Only
          </label>
        </div>
      </div>

      {/* Wi-Fi Table */}
      <div className="border border-slate-800 rounded-2xl overflow-hidden bg-slate-900/60 backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800 text-[11px]">
              <tr>
                <th className="py-3 px-4">SSID (Network Name)</th>
                <th className="py-3 px-4">BSSID (MAC)</th>
                <th className="py-3 px-4 text-center">Signal</th>
                <th className="py-3 px-4 text-center">Channel</th>
                <th className="py-3 px-4">Band</th>
                <th className="py-3 px-4">Security</th>
                <th className="py-3 px-4">Vendor</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredNetworks.map((net, idx) => {
                const isSelected = selectedNetwork?.bssid === net.bssid;
                return (
                  <tr
                    key={`${net.bssid}-${idx}`}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isSelected ? 'bg-blue-950/30' : ''
                    } ${net.is_tplink ? 'bg-blue-950/10' : ''}`}
                  >
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <Wifi className={`w-4 h-4 ${getSignalColor(net.signal)}`} />
                        <span className="font-semibold text-slate-100">{net.ssid}</span>
                        {net.is_tplink && (
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                            TP-LINK
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 font-mono text-slate-400">{net.bssid}</td>

                    <td className="py-3.5 px-4 text-center">
                      <span className={`font-mono font-bold ${getSignalColor(net.signal)}`}>
                        {net.signal}%
                      </span>
                      <div className="text-[10px] font-mono text-slate-500">{net.bars}</div>
                    </td>

                    <td className="py-3.5 px-4 text-center font-mono text-slate-300">
                      {net.channel || '-'}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px] font-mono">
                        {net.band}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-slate-300">
                        {net.security.includes('WPA') ? (
                          <Lock className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Unlock className="w-3.5 h-3.5 text-amber-400" />
                        )}
                        <span>{net.security}</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="text-slate-300 font-medium">{net.vendor}</span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedNetwork(net);
                          onNavigate('discovery');
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white border border-slate-700 hover:border-blue-500 transition-colors inline-flex items-center gap-1 text-[11px]"
                      >
                        Select AP
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Saved Profiles Section */}
      {savedProfiles.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-2 text-sm font-bold text-white mb-3">
            <Bookmark className="w-4 h-4 text-blue-400" />
            Configured Wi-Fi Connection Profiles on this Ubuntu Host
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {savedProfiles.map((p) => (
              <div
                key={p.uuid}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-200">{p.name}</div>
                  <div className="text-[10px] text-slate-500 font-mono truncate">{p.uuid.slice(0, 16)}...</div>
                </div>
                {p.active && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium">
                    Active
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

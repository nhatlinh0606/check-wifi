import React, { useState } from 'react';
import {
  KeyRound,
  RefreshCw,
  Search,
  Wifi,
  Lock,
  Unlock,
  CheckCircle2,
  Copy,
  Check,
  Eye,
  EyeOff,
  AlertCircle,
  ShieldCheck,
  HelpCircle,
  FileKey,
} from 'lucide-react';
import { WifiNetwork, PasswordTraceResult } from '../types';
import { traceWifiPassword } from '../services/api';

interface WifiPasswordRecoveryPageProps {
  networks: WifiNetwork[];
  isScanning: boolean;
  onRefreshNetworks: () => void;
}

export const WifiPasswordRecoveryPage: React.FC<WifiPasswordRecoveryPageProps> = ({
  networks,
  isScanning,
  onRefreshNetworks,
}) => {
  const [selectedNetwork, setSelectedNetwork] = useState<WifiNetwork | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isTracing, setIsTracing] = useState(false);
  const [traceResult, setTraceResult] = useState<PasswordTraceResult | null>(null);
  const [showPassword, setShowPassword] = useState(true);
  const [copied, setCopied] = useState(false);

  const filteredNetworks = networks.filter(
    (n) =>
      n.ssid.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.bssid.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.vendor.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelectNetwork = (net: WifiNetwork) => {
    setSelectedNetwork(net);
    setTraceResult(null);
    setCopied(false);
  };

  const handleTracePassword = async () => {
    if (!selectedNetwork) return;
    setIsTracing(true);
    setTraceResult(null);
    setCopied(false);

    try {
      const res = await traceWifiPassword(selectedNetwork.ssid, selectedNetwork.bssid);
      setTraceResult(res);
    } catch (err: any) {
      setTraceResult({
        found: false,
        ssid: selectedNetwork.ssid,
        bssid: selectedNetwork.bssid,
        message: err.message || 'Error tracing local password',
        explanation: 'Failed to query local NetworkManager. Please ensure appropriate system permissions.',
      });
    } finally {
      setIsTracing(false);
    }
  };

  const handleCopyPassword = (pwd: string) => {
    navigator.clipboard.writeText(pwd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const getSignalColor = (signal: number) => {
    if (signal >= 75) return 'text-emerald-400';
    if (signal >= 50) return 'text-blue-400';
    if (signal >= 30) return 'text-amber-400';
    return 'text-rose-400';
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900/50 via-indigo-900/40 to-slate-900/80 border border-blue-500/30">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0">
            <KeyRound className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Wi-Fi Password Recovery Scanner
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium">
                Localhost Authorized
              </span>
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Scan nearby Wi-Fi networks, select your network, and instantly check whether its password is
              stored locally in your Ubuntu NetworkManager connection store.
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Scanner, Right Trace Action & Result */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Wi-Fi Scanner (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Wifi className="w-4 h-4 text-blue-400" />
                  1. Scan & Select Wi-Fi Network
                </h3>
                <p className="text-xs text-slate-400">Click any network below to inspect credentials</p>
              </div>

              <button
                onClick={onRefreshNetworks}
                disabled={isScanning}
                className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-blue-600/20"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin' : ''}`} />
                {isScanning ? 'Scanning...' : 'Rescan Wi-Fi'}
              </button>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search by SSID, BSSID or Vendor..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Network List */}
            <div className="max-h-[460px] overflow-y-auto space-y-2 pr-1">
              {filteredNetworks.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">
                  {isScanning ? 'Scanning airwaves...' : 'No Wi-Fi networks found.'}
                </div>
              ) : (
                filteredNetworks.map((net) => {
                  const isSelected = selectedNetwork?.bssid === net.bssid;
                  return (
                    <div
                      key={net.bssid}
                      onClick={() => handleSelectNetwork(net)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-blue-950/60 border-blue-500 shadow-md shadow-blue-500/10'
                          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <Wifi className={`w-4 h-4 shrink-0 ${getSignalColor(net.signal)}`} />
                          <div>
                            <div className="font-semibold text-xs text-white flex items-center gap-2">
                              {net.ssid}
                              {net.is_tplink && (
                                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                  TP-LINK
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] font-mono text-slate-400">
                              {net.bssid} • Ch {net.channel} ({net.band})
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className={`font-mono text-xs font-bold ${getSignalColor(net.signal)}`}>
                            {net.signal}%
                          </div>
                          <div className="text-[10px] text-slate-400 flex items-center gap-1 justify-end">
                            {net.security.includes('WPA') ? (
                              <Lock className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Unlock className="w-3 h-3 text-amber-400" />
                            )}
                            <span className="truncate max-w-[80px]">{net.security}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Trace Action & Result Card (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-5">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileKey className="w-4 h-4 text-indigo-400" />
                2. Trace & Recover Password
              </h3>
              <p className="text-xs text-slate-400">Query local Ubuntu NetworkManager storage</p>
            </div>

            {selectedNetwork ? (
              <div className="space-y-4">
                {/* Selected Target Box */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-xs text-slate-400">Target Wi-Fi Network:</div>
                  <div className="font-bold text-base text-white flex items-center gap-2">
                    {selectedNetwork.ssid}
                    {selectedNetwork.is_tplink && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">
                        TP-Link
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-mono text-slate-400">
                    BSSID: <span className="text-slate-300">{selectedNetwork.bssid}</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Vendor: <span className="text-slate-200">{selectedNetwork.vendor}</span>
                  </div>
                </div>

                {/* Big Trace Action Button */}
                <button
                  onClick={handleTracePassword}
                  disabled={isTracing}
                  className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm tracking-wide shadow-xl shadow-blue-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  <KeyRound className={`w-4 h-4 ${isTracing ? 'animate-spin' : ''}`} />
                  {isTracing ? 'CHECKING LOCAL PROFILES...' : 'TRACE PASSWORD'}
                </button>

                {/* Tracing Progress Animation */}
                {isTracing && (
                  <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-800/40 text-center space-y-2 animate-pulse">
                    <div className="text-xs text-blue-300 font-semibold">
                      Querying local NetworkManager profiles...
                    </div>
                    <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full animate-indeterminate" />
                    </div>
                  </div>
                )}

                {/* Result Box */}
                {traceResult && (
                  <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                    {traceResult.found && traceResult.password ? (
                      /* Success: Password Found */
                      <div className="p-5 rounded-xl bg-emerald-950/40 border border-emerald-500/50 space-y-4 shadow-lg shadow-emerald-500/5">
                        <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
                          <CheckCircle2 className="w-4 h-4" />
                          Saved Password Recovered!
                        </div>

                        {/* Password Display Box */}
                        <div className="p-4 rounded-lg bg-slate-950 border border-emerald-500/30 space-y-2">
                          <div className="text-[11px] text-slate-400 flex items-center justify-between">
                            <span>Wi-Fi Pre-Shared Key (PSK):</span>
                            <button
                              onClick={() => setShowPassword(!showPassword)}
                              className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-[11px]"
                            >
                              {showPassword ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                              {showPassword ? 'Hide' : 'Show'}
                            </button>
                          </div>

                          <div className="font-mono font-bold text-lg text-white tracking-wider select-all break-all py-1">
                            {showPassword ? traceResult.password : '••••••••••••'}
                          </div>

                          <button
                            onClick={() => handleCopyPassword(traceResult.password!)}
                            className="w-full mt-2 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-emerald-600/20"
                          >
                            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                            {copied ? 'Password Copied to Clipboard!' : 'Copy Password'}
                          </button>
                        </div>

                        {/* Source Meta */}
                        <div className="space-y-1 text-[11px] text-slate-300 font-mono pt-1">
                          <div>
                            Source:{' '}
                            <span className="text-emerald-300 font-semibold">{traceResult.source}</span>
                          </div>
                          <div>
                            Profile Name:{' '}
                            <span className="text-slate-200">{traceResult.profile_name}</span>
                          </div>
                          <div>
                            Security Type:{' '}
                            <span className="text-slate-200">{traceResult.security_type || 'WPA2-PSK'}</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Not Found Alert */
                      <div className="p-5 rounded-xl bg-amber-950/30 border border-amber-500/40 space-y-3">
                        <div className="flex items-center gap-2 text-amber-400 font-bold text-xs uppercase tracking-wider">
                          <AlertCircle className="w-4 h-4 shrink-0" />
                          Password not found in local saved Wi-Fi profiles.
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed">
                          {traceResult.explanation}
                        </p>

                        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                          <div className="font-semibold text-slate-300 flex items-center gap-1">
                            <HelpCircle className="w-3.5 h-3.5 text-blue-400" />
                            Legitimate Recovery Options:
                          </div>
                          <div>• Check passwords saved on previously connected phones or laptops.</div>
                          <div>• Connect an Ethernet LAN cable to directly administer the router.</div>
                          <div>• Use the Remote Reset pinhole on the indoor PoE injector (Case E).</div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              /* No network selected empty state */
              <div className="p-8 text-center text-slate-500 text-xs rounded-xl bg-slate-950 border border-slate-800/80">
                <Wifi className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
                Select a Wi-Fi network from the list on the left to trace its saved password.
              </div>
            )}
          </div>

          {/* Security policy footnote */}
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-[11px] text-slate-400 flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              Credentials are read strictly from your local Ubuntu NetworkManager configuration files
              and are never sent over the network or uploaded to external servers.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

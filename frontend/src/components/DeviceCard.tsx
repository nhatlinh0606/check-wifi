import React from 'react';
import {
  Router,
  Server,
  Globe,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { DiscoveredDevice } from '../types';

interface DeviceCardProps {
  device: DiscoveredDevice;
  onInspect: (device: DiscoveredDevice) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device, onInspect }) => {
  const getConfidenceBadge = () => {
    switch (device.confidence) {
      case 'High':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'Medium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'Low':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      default:
        return 'bg-slate-700/30 text-slate-400 border-slate-700';
    }
  };

  return (
    <div
      className={`rounded-xl border p-5 transition-all duration-200 relative overflow-hidden bg-slate-900/80 backdrop-blur-sm hover:border-slate-600 ${
        device.is_tplink_candidate
          ? 'border-blue-500/40 shadow-lg shadow-blue-500/5'
          : 'border-slate-800'
      }`}
    >
      {/* Top Banner */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
              device.is_tplink_candidate
                ? 'bg-blue-600/20 border-blue-500/40 text-blue-400'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            {device.is_gateway ? (
              <Router className="w-5 h-5 text-indigo-400" />
            ) : (
              <Server className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-base text-white">
                {device.ip}
              </span>
              {device.is_gateway && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Gateway
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400 font-mono mt-0.5">
              {device.mac || 'MAC Unknown'}
            </div>
          </div>
        </div>

        {/* Confidence Badge */}
        <div className="text-right">
          <span
            className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full border ${getConfidenceBadge()}`}
          >
            {device.is_tplink_candidate ? (
              <ShieldCheck className="w-3 h-3" />
            ) : (
              <ShieldAlert className="w-3 h-3 text-slate-400" />
            )}
            {device.confidence} ({device.confidence_score}%)
          </span>
          <div className="text-[11px] text-slate-400 mt-1 font-medium">
            Vendor: <span className="text-slate-200">{device.detected_vendor}</span>
          </div>
        </div>
      </div>

      {/* Model hint or signatures */}
      {device.model_hint && (
        <div className="mb-3 px-3 py-1.5 rounded-lg bg-blue-950/40 border border-blue-800/40 text-xs text-blue-300 flex items-center justify-between">
          <span>Identified Model:</span>
          <span className="font-semibold text-white">{device.model_hint}</span>
        </div>
      )}

      {/* Ports and Admin link */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-slate-500 text-[11px]">Ports:</span>
          {device.open_ports.length > 0 ? (
            device.open_ports.map((port) => (
              <span
                key={port}
                className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[11px]"
              >
                {port}
              </span>
            ))
          ) : (
            <span className="text-slate-500 italic">None detected</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {device.admin_url && (
            <a
              href={device.admin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 hover:text-blue-300 border border-slate-700 transition-colors"
            >
              <Globe className="w-3 h-3" />
              Web Admin
              <ExternalLink className="w-3 h-3 opacity-60" />
            </a>
          )}

          <button
            onClick={() => onInspect(device)}
            className="flex items-center gap-1 px-3 py-1 rounded bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/40 transition-colors"
          >
            Inspect
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
};

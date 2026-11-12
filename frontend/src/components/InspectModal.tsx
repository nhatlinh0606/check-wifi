import React from 'react';
import {
  X,
  Router,
  Globe,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  LifeBuoy,
} from 'lucide-react';
import { DiscoveredDevice } from '../types';

interface InspectModalProps {
  device: DiscoveredDevice | null;
  onClose: () => void;
  onNavigateToRecovery: (caseId: string) => void;
}

export const InspectModal: React.FC<InspectModalProps> = ({
  device,
  onClose,
  onNavigateToRecovery,
}) => {
  if (!device) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <Router className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                Device Diagnostics: {device.ip}
                {device.is_gateway && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                    Default Gateway
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                MAC: {device.mac || 'N/A'} • Vendor: {device.detected_vendor}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {/* Status summary banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">TP-Link Candidate</div>
              <div className="font-bold text-base flex items-center gap-2">
                {device.is_tplink_candidate ? (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4" /> Yes
                  </span>
                ) : (
                  <span className="text-slate-400 flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4 text-amber-400" /> Third-party / Other
                  </span>
                )}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Confidence Score</div>
              <div className="font-bold text-base text-blue-400 flex items-center justify-between">
                <span>{device.confidence}</span>
                <span className="font-mono text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30">
                  {device.confidence_score}%
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Detected Model</div>
              <div className="font-bold text-base text-slate-100 truncate">
                {device.model_hint || 'Standard Firmware'}
              </div>
            </div>
          </div>

          {/* Evidence List */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Diagnostic Evidence & Indicators
            </h3>
            <div className="space-y-2">
              {device.evidence.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 text-xs text-slate-300 flex items-start gap-2.5"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* HTTP/HTTPS Web Admin Endpoints */}
          {device.details?.endpoints && device.details.endpoints.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                Web Management Endpoints
              </h3>
              <div className="space-y-3">
                {device.details.endpoints.map((ep, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold uppercase px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono text-[11px]">
                          {ep.protocol} (Port {ep.port})
                        </span>
                        <span className="font-mono text-slate-300">{ep.url}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">
                        HTTP {ep.status_code}
                      </span>
                    </div>

                    {ep.title && (
                      <div className="text-slate-400">
                        Page Title:{' '}
                        <span className="text-slate-200 font-medium">{ep.title}</span>
                      </div>
                    )}

                    {ep.final_url && ep.final_url !== ep.url && (
                      <div className="text-slate-400">
                        Redirect Target:{' '}
                        <span className="text-slate-300 font-mono">{ep.final_url}</span>
                      </div>
                    )}

                    {ep.tplink_signatures_found.length > 0 && (
                      <div className="text-slate-400">
                        Signatures:{' '}
                        <span className="text-blue-300 font-medium">
                          {ep.tplink_signatures_found.join(', ')}
                        </span>
                      </div>
                    )}

                    <div className="pt-2 flex justify-end">
                      <a
                        href={ep.final_url || ep.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors text-xs"
                      >
                        <Globe className="w-3.5 h-3.5" />
                        Open Web Portal
                        <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Recovery Recommendations */}
          <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-900/40">
            <div className="flex items-center gap-2 text-blue-300 font-semibold mb-2">
              <LifeBuoy className="w-4 h-4 text-blue-400" />
              Need to restore administrative access?
            </div>
            <p className="text-xs text-slate-300 mb-3">
              If the password or IP configuration was modified, choose an official recovery
              option tailored to your router:
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  onClose();
                  onNavigateToRecovery('A');
                }}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700"
              >
                Case A: Forgot Password
              </button>
              <button
                onClick={() => {
                  onClose();
                  onNavigateToRecovery('E');
                }}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-amber-300 border border-slate-700"
              >
                Case E: Factory Reset / PoE Remote Reset
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

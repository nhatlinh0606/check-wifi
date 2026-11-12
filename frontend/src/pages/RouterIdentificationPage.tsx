import React from 'react';
import {
  Radio,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Globe,
  Server,
  Info,
} from 'lucide-react';
import { FullDiagnosisResult } from '../types';

interface RouterIdentificationPageProps {
  latestDiagnosis: FullDiagnosisResult | null;
}

export const RouterIdentificationPage: React.FC<RouterIdentificationPageProps> = ({
  latestDiagnosis,
}) => {
  const routerData = latestDiagnosis?.router_identification;
  const mgmtData = latestDiagnosis?.management;
  const plan = latestDiagnosis?.recovery_plan;

  const endpoints = mgmtData?.management_endpoints || [];
  const candidateDevices = routerData?.candidate_devices || [];

  return (
    <div className="space-y-6">
      {/* Confirmed Facts vs Hypotheses Callout Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Confirmed Facts */}
        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            Confirmed Facts (Verified by Network Telemetry)
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {plan?.confirmed_facts?.length ? (
              plan.confirmed_facts.map((fact, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{fact}</span>
                </li>
              ))
            ) : (
              <li className="text-slate-500 italic">Run Automatic Diagnosis to confirm network facts.</li>
            )}
          </ul>
        </div>

        {/* Working Hypotheses & Unknowns */}
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            Working Hypotheses & Unknown Variables
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {plan?.working_hypotheses?.map((hyp, idx) => (
              <li key={`h-${idx}`} className="flex items-start gap-2">
                <span className="text-amber-400 font-bold">~</span>
                <span>{hyp}</span>
              </li>
            ))}
            {plan?.unknown_variables?.map((unk, idx) => (
              <li key={`u-${idx}`} className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">?</span>
                <span className="text-slate-400">{unk}</span>
              </li>
            ))}
            {!plan && (
              <li className="text-slate-500 italic">No hypotheses evaluated yet.</li>
            )}
          </ul>
        </div>
      </div>

      {/* Gateway Device Identity Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <div className="text-base font-bold text-white flex items-center gap-2">
                Gateway Device Identification
                {routerData?.is_tplink_candidate && (
                  <span className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold border border-blue-500/30">
                    TP-Link Candidate
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                Identified via ARP OUI lookup, open service probe, and HTTP response signatures
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Confidence:</span>
            <span
              className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
                plan?.confidence_rating === 'High'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : plan?.confidence_rating === 'Medium'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {plan?.confidence_rating || 'Pending'}
            </span>
          </div>
        </div>

        {/* Identity Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-500 uppercase font-semibold">Gateway IP</div>
            <div className="text-base font-mono font-bold text-white mt-1">
              {mgmtData?.gateway_ip || latestDiagnosis?.routing?.default_gateway || 'Unknown'}
            </div>
          </div>

          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-500 uppercase font-semibold">Gateway MAC</div>
            <div className="text-base font-mono font-bold text-slate-300 mt-1">
              {routerData?.gateway_device?.mac || 'Unknown'}
            </div>
          </div>

          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-500 uppercase font-semibold">Detected Vendor</div>
            <div className="text-base font-bold text-purple-300 mt-1 truncate">
              {routerData?.detected_vendor || 'Unknown'}
            </div>
          </div>

          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
            <div className="text-[11px] text-slate-500 uppercase font-semibold">Model Hint</div>
            <div className="text-base font-mono font-bold text-amber-300 mt-1">
              {mgmtData?.model_hint || 'Standard TP-Link / SOHO'}
            </div>
          </div>
        </div>
      </div>

      {/* Stage C: Management Web Portals & Clickable Links */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Globe className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Management Web Interfaces (HTTP / HTTPS)
            </h3>
          </div>
          <div className="text-xs text-slate-400">
            Management Reachable:{' '}
            <span className={`font-semibold ${mgmtData?.is_management_reachable ? 'text-emerald-400' : 'text-slate-400'}`}>
              {mgmtData?.is_management_reachable ? 'Yes (Responding)' : 'No'}
            </span>
          </div>
        </div>

        {endpoints.length === 0 ? (
          <div className="p-6 text-center rounded-xl bg-slate-950/40 border border-slate-800/60 text-slate-400 text-xs">
            No management web endpoints discovered yet.
            {mgmtData?.gateway_ip ? (
              <p className="mt-1 text-slate-500">
                Ports 80/443 did not respond on {mgmtData.gateway_ip}. Connect over Ethernet or check if management IP was changed.
              </p>
            ) : (
              <p className="mt-1 text-slate-500">Run an Automatic Diagnosis to discover open management ports.</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {endpoints.map((ep, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950/80 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-blue-500/40 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-white text-sm">{ep.url}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-semibold">
                      HTTP {ep.status_code}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      Port {ep.port} ({ep.protocol.toUpperCase()})
                    </span>
                  </div>

                  <div className="text-xs text-slate-300">
                    <span className="text-slate-500">Page Title: </span>
                    <span className="font-semibold">{ep.title || 'Untitled Portal'}</span>
                  </div>

                  {ep.server_header && (
                    <div className="text-[11px] text-slate-400 font-mono">
                      Server Header: {ep.server_header}
                    </div>
                  )}

                  {ep.tplink_signatures_found?.length > 0 && (
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="text-[10px] text-slate-500">Signatures:</span>
                      {ep.tplink_signatures_found.map((sig, sidx) => (
                        <span key={sidx} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 font-mono">
                          {sig}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <a
                    href={ep.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all shadow-md shadow-blue-600/20"
                  >
                    Open Router Portal
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Security Notice regarding web authentication */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
          <Info className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
          <span>
            Clicking &quot;Open Router Portal&quot; will launch the management login page in your default browser.
            The recovery toolkit strictly avoids automated password guessing, brute-forcing, or credential spraying.
          </span>
        </div>
      </div>

      {/* Discovered Subnet Devices */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Discovered Subnet Devices ({candidateDevices.length})
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">ARP sweep & port assessment</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Device IP</th>
                <th className="py-3 px-4">MAC Address</th>
                <th className="py-3 px-4">Vendor Resolution</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Open Ports</th>
                <th className="py-3 px-4">TP-Link Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {candidateDevices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    No devices mapped on local subnet yet.
                  </td>
                </tr>
              ) : (
                candidateDevices.map((dev, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-3 px-4 font-mono font-bold text-white">{dev.ip}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{dev.mac || 'N/A'}</td>
                    <td className="py-3 px-4 font-medium">{dev.detected_vendor}</td>
                    <td className="py-3 px-4">
                      {dev.is_gateway ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold text-[11px]">
                          Default Gateway
                        </span>
                      ) : (
                        <span className="text-slate-500">Local Host</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {dev.open_ports?.length ? dev.open_ports.join(', ') : 'None'}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {dev.confidence_score > 0 ? (
                        <span className="text-blue-400 font-bold">{dev.confidence_score}% ({dev.confidence})</span>
                      ) : (
                        <span className="text-slate-500">0%</span>
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
  );
};

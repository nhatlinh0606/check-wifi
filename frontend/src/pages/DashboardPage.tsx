import React from 'react';
import {
  Play,
  Square,
  ShieldCheck,
  Wifi,
  Network,
  Radio,
  FileKey,
  Compass,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Loader2,
  Layers,
} from 'lucide-react';
import { DiagnosisStatus, FullDiagnosisResult, PageId } from '../types';

interface DashboardPageProps {
  diagnosisStatus: DiagnosisStatus;
  latestDiagnosis: FullDiagnosisResult | null;
  onStartDiagnosis: () => void;
  onStopDiagnosis: () => void;
  onSelectPage: (page: PageId) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  diagnosisStatus,
  latestDiagnosis,
  onStartDiagnosis,
  onStopDiagnosis,
  onSelectPage,
}) => {
  const isRunning = diagnosisStatus.status === 'running';
  const plan = latestDiagnosis?.recovery_plan;
  const routing = latestDiagnosis?.routing;
  const routerId = latestDiagnosis?.router_identification;

  return (
    <div className="space-y-6">
      {/* Primary Action Card: Autonomous Diagnosis CTA */}
      <div className="relative overflow-hidden rounded-2xl border border-blue-500/30 bg-gradient-to-br from-slate-900 via-blue-950/30 to-slate-900 p-6 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/30 text-blue-300 text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              Autonomous Router Discovery & Recovery Engine
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              One-Click Router Diagnostic & Recovery Assistant
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Automatically discovers local network interfaces, analyzes wireless airwaves, maps gateway routing,
              inspects router management portals, audits authorized local credential stores, and generates a concrete
              hardware recovery plan.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {isRunning ? (
              <button
                onClick={onStopDiagnosis}
                className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all cursor-pointer"
              >
                <Square className="w-4 h-4 fill-white" />
                Cancel Diagnosis
              </button>
            ) : (
              <button
                onClick={onStartDiagnosis}
                className="flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl text-sm font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
              >
                <Play className="w-4 h-4 fill-white" />
                Start Automatic Diagnosis
              </button>
            )}

            {plan && (
              <button
                onClick={() => onSelectPage('recovery-plan')}
                className="flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl text-sm font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all cursor-pointer"
              >
                View Current Plan
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Real-time Status Banner */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5 text-slate-300">
            {isRunning ? (
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            )}
            <span className="font-medium text-slate-200">Status:</span>
            <span className="font-mono text-blue-300">{diagnosisStatus.stage_message}</span>
          </div>

          <div className="text-slate-400 flex items-center gap-2">
            <span>Mode:</span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              Passive & Localhost Only (No brute-force)
            </span>
          </div>
        </div>
      </div>

      {/* 8-Stage Visual Progress Stepper */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <Layers className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Autonomous Pipeline Stepper (8 Stages)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {diagnosisStatus.current_stage > 0 ? `Stage ${diagnosisStatus.current_stage} of 8` : 'Idle'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {diagnosisStatus.stages.map((stg) => {
            const isCompleted = stg.status === 'completed';
            const isActive = stg.status === 'active';
            const isFailed = stg.status === 'failed';

            return (
              <div
                key={stg.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  isActive
                    ? 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/10'
                    : isCompleted
                    ? 'border-emerald-500/30 bg-emerald-500/5'
                    : isFailed
                    ? 'border-rose-500/30 bg-rose-500/5'
                    : 'border-slate-800/80 bg-slate-950/40 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      isActive
                        ? 'bg-blue-500/20 text-blue-300'
                        : isCompleted
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    Stage {stg.id}
                  </span>
                  {isActive && <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />}
                  {isCompleted && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  {isFailed && <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />}
                  {!isActive && !isCompleted && !isFailed && <Clock className="w-3.5 h-3.5 text-slate-600" />}
                </div>
                <div className={`text-xs font-semibold ${isActive ? 'text-white' : isCompleted ? 'text-slate-200' : 'text-slate-400'}`}>
                  {stg.name}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Telemetry Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Connection Medium */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Connection Medium</span>
            <Network className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-lg font-bold text-white capitalize">
            {routing?.connection_type || 'Unknown'}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-mono">
            Dev: {routing?.gateway_interface || 'Not detected'}
          </div>
        </div>

        {/* Gateway Management IP */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Gateway IP</span>
            <Compass className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400 font-mono">
            {routing?.default_gateway || 'No Gateway'}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-mono">
            Subnet: {routing?.target_subnet || 'N/A'}
          </div>
        </div>

        {/* Router Vendor & OUI */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Detected Vendor</span>
            <Radio className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-lg font-bold text-white truncate">
            {routerId?.detected_vendor || 'Unknown'}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
            <span>TP-Link match:</span>
            <span className={`font-semibold ${routerId?.is_tplink_candidate ? 'text-emerald-400' : 'text-slate-400'}`}>
              {routerId?.is_tplink_candidate ? 'Yes (Candidate)' : 'No'}
            </span>
          </div>
        </div>

        {/* Recovery Scenario Recommendation */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Decision Scenario</span>
            <FileKey className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-base font-bold text-amber-400 truncate">
            {plan ? plan.scenario_title.split(':')[0] : 'Pending Diagnosis'}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span>Confidence:</span>
            <span className="font-semibold text-slate-200">{plan?.confidence_rating || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Decision Engine Summary Banner (When Result Ready) */}
      {plan && (
        <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                <FileKey className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white">{plan.scenario_title}</h4>
                <p className="text-xs text-slate-300">{plan.scenario_summary}</p>
              </div>
            </div>
            <button
              onClick={() => onSelectPage('recovery-plan')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all cursor-pointer self-start sm:self-auto"
            >
              Step-by-step Action Plan
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Confirmed facts snapshot */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-slate-800">
            <div>
              <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
                Confirmed Facts ({plan.confirmed_facts.length})
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {plan.confirmed_facts.slice(0, 3).map((f, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
                Key Action Recommendations
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {plan.action_steps.slice(0, 3).map((s) => (
                  <li key={s.step} className="flex items-start gap-2">
                    <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-300 font-mono text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                      {s.step}
                    </span>
                    <span className="font-medium text-slate-200">{s.title}:</span>
                    <span className="text-slate-400 truncate">{s.instruction}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Quick Jump Stage Exploration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Network Discovery */}
        <div
          onClick={() => onSelectPage('network-discovery')}
          className="bg-slate-900/40 border border-slate-800 hover:border-blue-500/50 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-800/40 group"
        >
          <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-3 group-hover:scale-110 transition-transform">
            <Wifi className="w-4 h-4" />
          </div>
          <div className="font-bold text-sm text-white group-hover:text-blue-400 transition-colors">
            Stage A: Network Discovery
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Wireless environment, nearby SSIDs, system network interfaces, controller chipsets, and routing table.
          </p>
          <div className="mt-3 text-xs text-blue-400 font-semibold flex items-center gap-1">
            Explore topology <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Router Identification */}
        <div
          onClick={() => onSelectPage('router-identification')}
          className="bg-slate-900/40 border border-slate-800 hover:border-purple-500/50 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-800/40 group"
        >
          <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-3 group-hover:scale-110 transition-transform">
            <Radio className="w-4 h-4" />
          </div>
          <div className="font-bold text-sm text-white group-hover:text-purple-400 transition-colors">
            Stage B & C: Router ID & Web UI
          </div>
          <p className="text-xs text-slate-400 mt-1">
            MAC OUI resolution, port scanning, web server headers, auth realms, model signatures, and direct web links.
          </p>
          <div className="mt-3 text-xs text-purple-400 font-semibold flex items-center gap-1">
            Inspect device <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Credential Recovery */}
        <div
          onClick={() => onSelectPage('credential-recovery')}
          className="bg-slate-900/40 border border-slate-800 hover:border-emerald-500/50 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-800/40 group"
        >
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-3 group-hover:scale-110 transition-transform">
            <FileKey className="w-4 h-4" />
          </div>
          <div className="font-bold text-sm text-white group-hover:text-emerald-400 transition-colors">
            Stage D: Credential Audit
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Audit local NetworkManager profiles, keyfiles, router backup archives, and upload configuration files.
          </p>
          <div className="mt-3 text-xs text-emerald-400 font-semibold flex items-center gap-1">
            Audit local stores <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Recovery Plan */}
        <div
          onClick={() => onSelectPage('recovery-plan')}
          className="bg-slate-900/40 border border-slate-800 hover:border-amber-500/50 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-800/40 group"
        >
          <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-3 group-hover:scale-110 transition-transform">
            <Compass className="w-4 h-4" />
          </div>
          <div className="font-bold text-sm text-white group-hover:text-amber-400 transition-colors">
            Stage E: Recovery Plan
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Decision tree output (Scenarios 1-5), factory reset procedures, ISP VLAN warning, and pole PoE remote reset.
          </p>
          <div className="mt-3 text-xs text-amber-400 font-semibold flex items-center gap-1">
            Execute recovery <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>

      {/* Security & Technical Integrity Notice */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 flex items-start gap-3 text-xs text-slate-400">
        <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-200">Ethical & Passive Operating Standard: </span>
          This toolkit is designed exclusively for network equipment you own or are authorized to manage.
          Passive Wi-Fi beacon inspection does not and cannot extract WPA2 pre-shared keys due to cryptographic 4-way handshake design.
          No brute-force or authentication bypass is performed. Recovery is achieved through confirmed local network facts,
          legitimate local credential caches, or official hardware reset mechanisms.
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  Compass,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Copy,
  Check,
  ExternalLink,
  Terminal,
  Layers,
} from 'lucide-react';
import { FullDiagnosisResult, RecoveryPlan } from '../types';

interface RecoveryPlanPageProps {
  latestDiagnosis: FullDiagnosisResult | null;
}

export const RecoveryPlanPage: React.FC<RecoveryPlanPageProps> = ({
  latestDiagnosis,
}) => {
  const [copiedCmd, setCopiedCmd] = useState<number | null>(null);

  const plan: RecoveryPlan | undefined = latestDiagnosis?.recovery_plan;

  const copyCommand = (cmd: string, idx: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(idx);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  if (!plan) {
    return (
      <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <Compass className="w-12 h-12 text-slate-500 mx-auto" />
        <h3 className="text-lg font-bold text-white">No Recovery Plan Generated Yet</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Please run an Automatic Diagnosis from the Dashboard to synthesize network telemetry into an actionable recovery plan.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Active Scenario Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-amber-500/40 bg-gradient-to-br from-slate-900 via-amber-950/20 to-slate-900 p-6 shadow-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
              <Compass className="w-3.5 h-3.5" />
              Active Recovery Scenario: {plan.scenario_id.toUpperCase()}
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              {plan.scenario_title}
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
              {plan.scenario_summary}
            </p>
          </div>

          <div className="flex flex-col items-start sm:items-end gap-1">
            <span className="text-xs text-slate-400">Diagnosis Confidence</span>
            <span
              className={`px-3 py-1 rounded-lg text-xs font-bold font-mono ${
                plan.confidence_rating === 'High'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : plan.confidence_rating === 'Medium'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {plan.confidence_rating} Confidence
            </span>
          </div>
        </div>
      </div>

      {/* Tri-Column: Facts vs Hypotheses vs Unknowns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Confirmed Facts */}
        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            Confirmed Facts ({plan.confirmed_facts?.length || 0})
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {plan.confirmed_facts?.map((f, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">•</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Working Hypotheses */}
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            Working Hypotheses ({plan.working_hypotheses?.length || 0})
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {plan.working_hypotheses?.map((h, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-amber-400 font-bold">~</span>
                <span>{h}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Unknown Variables */}
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-rose-400 uppercase tracking-wider">
            <AlertOctagon className="w-4 h-4" />
            Unknown Variables ({plan.unknown_variables?.length || 0})
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {plan.unknown_variables?.map((u, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">?</span>
                <span>{u}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Actionable Step-by-Step Recovery Procedure */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <Compass className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Step-by-Step Action Plan
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {plan.action_steps?.length || 0} Recommended Actions
          </span>
        </div>

        <div className="space-y-4">
          {plan.action_steps?.map((step) => (
            <div
              key={step.step}
              className="p-4 rounded-xl border border-slate-800 bg-slate-950/80 space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 font-mono text-xs flex items-center justify-center shrink-0 font-bold mt-0.5">
                  {step.step}
                </span>
                <div className="space-y-1 flex-1">
                  <div className="text-sm font-bold text-white">{step.title}</div>
                  <p className="text-xs text-slate-300 leading-relaxed">{step.instruction}</p>
                </div>
              </div>

              {step.command && (
                <div className="mt-2 pl-9">
                  <div className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-emerald-400">
                    <div className="flex items-center gap-2 truncate">
                      <Terminal className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span className="truncate">{step.command}</span>
                    </div>
                    <button
                      onClick={() => copyCommand(step.command!, step.step)}
                      className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 shrink-0"
                      title="Copy Command"
                    >
                      {copiedCmd === step.step ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {step.caution && (
                <div className="mt-2 pl-9">
                  <div className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span>{step.caution}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>


      {/* Critical ISP VLAN & PPPoE Warning Card */}
      <div className="p-5 rounded-2xl border border-rose-500/40 bg-rose-500/5 space-y-3">
        <div className="flex items-center gap-2.5 text-sm font-bold text-rose-400 uppercase tracking-wider">
          <AlertOctagon className="w-4 h-4" />
          Critical ISP Configuration Warning Before Factory Reset
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          {plan.isp_pppoe_warning}
        </p>
      </div>

      {/* Hardware Model Reset Timings Card */}
      {plan.model_specific_reset && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-purple-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Hardware Reset Specifications ({plan.model_specific_reset.model})
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <div className="text-[11px] text-slate-500 uppercase font-semibold">Hold Duration</div>
              <div className="text-base font-mono font-bold text-amber-400 mt-1">
                {plan.model_specific_reset.hold_duration_sec} Seconds
              </div>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <div className="text-[11px] text-slate-500 uppercase font-semibold">LED Behavior</div>
              <div className="text-xs text-slate-300 mt-1">
                {plan.model_specific_reset.led_indicator}
              </div>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <div className="text-[11px] text-slate-500 uppercase font-semibold">Default IP / Web</div>
              <div className="text-xs font-mono font-bold text-emerald-400 mt-1">
                {plan.model_specific_reset.default_ip} ({plan.model_specific_reset.default_web_url})
              </div>
            </div>

            <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
              <div className="text-[11px] text-slate-500 uppercase font-semibold">Default Credentials</div>
              <div className="text-xs font-mono font-bold text-white mt-1">
                {plan.model_specific_reset.default_credentials}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Official Documentation Links */}
      {plan.official_vendor_docs?.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-2.5">
            <ExternalLink className="w-5 h-5 text-blue-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Official TP-Link Documentation & Knowledge Base
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {plan.official_vendor_docs.map((doc, idx) => (
              <a
                key={idx}
                href={doc.url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 rounded-xl border border-slate-800 bg-slate-950 hover:border-blue-500/50 flex items-center justify-between text-xs text-slate-300 hover:text-white transition-all group"
              >
                <span>{doc.title}</span>
                <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

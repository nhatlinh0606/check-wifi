import React, { useState } from 'react';
import { LifeBuoy, Cpu } from 'lucide-react';
import { RecoveryCase } from '../types';

interface RecoveryPageProps {
  cases: Record<string, RecoveryCase>;
  initialCase?: string;
}

export const RecoveryPage: React.FC<RecoveryPageProps> = ({ cases, initialCase = 'A' }) => {
  const [selectedCase, setSelectedCase] = useState<string>(initialCase);

  const activeCaseData = cases[selectedCase] || cases['A'];

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-slate-900/70 border border-blue-500/30">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0">
            <LifeBuoy className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              TP-Link Credential & Access Recovery Assistant
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              When router management passwords or LAN configurations are forgotten or modified,
              follow authorized manufacturer recovery workflows. This assistant provides verified
              physical and software restoration procedures without risky or invasive operations.
            </p>
          </div>
        </div>
      </div>

      {/* Case Navigation Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {Object.keys(cases).map((key) => {
          const item = cases[key];
          const isSelected = selectedCase === key;
          return (
            <button
              key={key}
              onClick={() => setSelectedCase(key)}
              className={`p-3 rounded-xl border text-left transition-all ${
                isSelected
                  ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-600/20'
                  : 'bg-slate-900/70 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <div className="font-bold text-xs uppercase tracking-wider mb-1">
                Case {key}
              </div>
              <div className="text-[11px] font-medium line-clamp-1">
                {item.title.replace(/^Case [A-E]:\s*/, '')}
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Case Instructions Panel */}
      {activeCaseData && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-1">
              Active Workflow Procedure
            </div>
            <h3 className="text-lg font-bold text-white">{activeCaseData.title}</h3>
            <p className="text-xs text-slate-400 mt-1">{activeCaseData.summary}</p>
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {activeCaseData.steps.map((step, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans"
              >
                {step.startsWith('1.') || step.startsWith('2.') || step.startsWith('3.') || step.startsWith('4.') || step.startsWith('5.') ? (
                  <div className="font-bold text-blue-300 mb-1">{step}</div>
                ) : (
                  <div className="pl-4 text-slate-300">{step}</div>
                )}
              </div>
            ))}
          </div>

          {/* Model Hardware Reset Table */}
          {selectedCase === 'E' && (
            <div className="pt-4 border-t border-slate-800">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-amber-400" />
                TP-Link Model Reset Timing & Default Settings
              </h4>
              <div className="border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 text-[11px] uppercase">
                    <tr>
                      <th className="py-2.5 px-4">Hardware Series</th>
                      <th className="py-2.5 px-4">Button Duration</th>
                      <th className="py-2.5 px-4">Default Admin IP / URL</th>
                      <th className="py-2.5 px-4">Initial Credentials</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    <tr>
                      <td className="py-2.5 px-4 font-semibold text-white">Archer Series (AX / C)</td>
                      <td className="py-2.5 px-4">8 - 10 seconds</td>
                      <td className="py-2.5 px-4 font-mono text-blue-400">192.168.0.1 / tplinkwifi.net</td>
                      <td className="py-2.5 px-4">Prompts to set password on 1st login</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-semibold text-white">TL-WR / TL-WDR Series</td>
                      <td className="py-2.5 px-4">6 - 8 seconds</td>
                      <td className="py-2.5 px-4 font-mono text-blue-400">192.168.0.1 or 192.168.1.1</td>
                      <td className="py-2.5 px-4 font-mono">admin / admin</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-4 font-semibold text-white">Deco Mesh System</td>
                      <td className="py-2.5 px-4">1 second (bottom)</td>
                      <td className="py-2.5 px-4">Configured via Deco Mobile App</td>
                      <td className="py-2.5 px-4">TP-Link Cloud ID</td>
                    </tr>

                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

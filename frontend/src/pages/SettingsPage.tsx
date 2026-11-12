import React from 'react';
import { Settings, Shield, Cpu, CheckCircle2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-400" />
            Toolkit Settings & Security Boundaries
          </h2>
          <p className="text-xs text-slate-400">
            Local server operational boundaries, authentication requirements, and diagnostic limits
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Security & Access Boundaries */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-4">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Shield className="w-4 h-4 text-emerald-400" />
            Security Architecture & Localhost Policy
          </div>
          <div className="space-y-3 text-xs text-slate-300">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong>Localhost Binding:</strong> The backend binds strictly to{' '}
                <code className="text-blue-400 bg-slate-950 px-1.5 py-0.5 rounded font-mono">127.0.0.1</code>{' '}
                preventing unauthorized access from external networks.
              </span>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong>No Arbitrary Command Execution:</strong> All scanning operations use typed, strictly
                sanitized parameters (IP address & interface regex validation).
              </span>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong>Non-Destructive & Passive:</strong> No brute-force, no dictionary attacks, no
                packet deauthentication, and no configuration overwrites.
              </span>
            </div>
          </div>
        </div>

        {/* Runtime Environment */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-4">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Cpu className="w-4 h-4 text-indigo-400" />
            Runtime Environment
          </div>
          <div className="space-y-2.5 text-xs text-slate-300">
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Host OS:</span>
              <span className="font-mono text-slate-200">Ubuntu Linux</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Backend Framework:</span>
              <span className="font-mono text-slate-200">FastAPI (Python 3.12)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Frontend Engine:</span>
              <span className="font-mono text-slate-200">React 18 + Vite + Tailwind CSS</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800">
              <span className="text-slate-400">Real-Time Transport:</span>
              <span className="font-mono text-emerald-400">WebSockets (/ws/scan)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">OUI Database:</span>
              <span className="font-mono text-slate-200">176 TP-Link OUIs (IEEE MA-L)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

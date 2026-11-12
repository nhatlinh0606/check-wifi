import React from 'react';
import {
  LayoutDashboard,
  Network,
  Wifi,
  Radio,
  History,
  LifeBuoy,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { PageId, NetworkInterface } from '../types';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  activeInterface?: NetworkInterface | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  activeInterface,
}) => {
  const navItems = [
    { id: 'dashboard' as PageId, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'interfaces' as PageId, label: 'Network Interfaces', icon: Network },
    { id: 'wifi' as PageId, label: 'Wi-Fi Discovery', icon: Wifi },
    { id: 'discovery' as PageId, label: 'Router Discovery', icon: Radio },
    { id: 'history' as PageId, label: 'Scan History', icon: History },
    { id: 'recovery' as PageId, label: 'Recovery Assistant', icon: LifeBuoy },
    { id: 'settings' as PageId, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950/80 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800">
          <div className="w-9 h-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="font-bold text-sm tracking-wide text-white flex items-center gap-2">
              TP-Link Toolkit
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono">
                v2.0
              </span>
            </div>
            <div className="text-xs text-slate-400">Router Recovery UI</div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectPage(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/25'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Interface Status */}
      <div className="p-4 border-t border-slate-800 m-3 rounded-xl bg-slate-900/60 border">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 mb-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          Authorized Diagnostic
        </div>
        {activeInterface ? (
          <div className="space-y-1 text-[11px] text-slate-400">
            <div className="flex justify-between">
              <span>Interface:</span>
              <span className="font-mono text-slate-200">{activeInterface.name}</span>
            </div>
            <div className="flex justify-between">
              <span>Local IP:</span>
              <span className="font-mono text-slate-200">{activeInterface.ip}</span>
            </div>
            <div className="flex justify-between">
              <span>Gateway:</span>
              <span className="font-mono text-emerald-400">
                {activeInterface.gateway || 'N/A'}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-xs text-amber-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            Detecting network...
          </div>
        )}
      </div>
    </aside>
  );
};

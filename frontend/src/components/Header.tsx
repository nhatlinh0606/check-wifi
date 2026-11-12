import React from 'react';
import { RefreshCw, Globe, KeyRound } from 'lucide-react';
import { PageId } from '../types';

interface HeaderProps {
  currentPage: PageId;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onRefresh,
  isRefreshing,
}) => {
  const titles: Partial<Record<PageId, { title: string; subtitle: string }>> = {
    'wifi-recovery': {
      title: 'Wi-Fi Password Recovery',
      subtitle: 'Select a Wi-Fi network, analyze security, and recover genuinely available credentials',
    },
    'credential-recovery': {
      title: 'Offline Backup Analyzer',
      subtitle: 'Extract wireless passphrases and network parameters from exported router configurations',
    },
    auditor: {
      title: 'Password Security Auditor',
      subtitle: 'Offline entropy evaluation, strong WPA2/WPA3 key generation, and dictionary wordlist analysis',
    },
    settings: {
      title: 'Settings & Security Policy',
      subtitle: 'Local server status, wireless interface binding, and authorized recovery guidelines',
    },
  };

  const { title, subtitle } = titles[currentPage] || {
    title: 'Wi-Fi Password Recovery',
    subtitle: 'Select a Wi-Fi network, analyze security, and recover genuinely available credentials',
  };

  return (
    <header className="h-16 px-8 border-b border-slate-800 bg-slate-900/40 backdrop-blur flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-base font-bold text-white flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-blue-400" />
          {title}
        </h1>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800 cursor-pointer"
          title="Refresh view data"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
        </button>

        <div className="h-6 w-px bg-slate-800 mx-1" />

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
          <Globe className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-mono text-slate-300">127.0.0.1:8000</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
        </div>
      </div>
    </header>
  );
};

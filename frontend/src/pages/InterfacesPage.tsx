import React from 'react';
import { Network, CheckCircle2, ArrowRight } from 'lucide-react';
import { NetworkInterface, PageId } from '../types';

interface InterfacesPageProps {
  interfaces: NetworkInterface[];
  selectedInterface: string | null;
  onSelectInterface: (ifaceName: string) => void;
  onNavigate: (page: PageId) => void;
}

export const InterfacesPage: React.FC<InterfacesPageProps> = ({
  interfaces,
  selectedInterface,
  onSelectInterface,
  onNavigate,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white">System Network Controllers</h2>
          <p className="text-xs text-slate-400">
            Detected IPv4 interfaces, subnet boundaries, and hardware MAC addresses
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {interfaces.map((iface) => {
          const isSelected = selectedInterface === iface.name;
          return (
            <div
              key={iface.name}
              className={`p-6 rounded-2xl border transition-all duration-200 bg-slate-900/60 backdrop-blur-sm ${
                isSelected
                  ? 'border-blue-500 shadow-lg shadow-blue-500/10 bg-slate-900'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center border ${
                      iface.is_up
                        ? 'bg-blue-600/20 border-blue-500/40 text-blue-400'
                        : 'bg-slate-800 border-slate-700 text-slate-500'
                    }`}
                  >
                    <Network className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="font-mono font-bold text-base text-white flex items-center gap-2">
                      {iface.name}
                      {iface.is_default && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          Default Route
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">
                      MAC: {iface.mac || 'N/A'}
                    </div>
                  </div>
                </div>

                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1 border ${
                    iface.is_up
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-slate-800 text-slate-500 border-slate-700'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      iface.is_up ? 'bg-emerald-400' : 'bg-slate-500'
                    }`}
                  />
                  {iface.is_up ? 'Link UP' : 'DOWN'}
                </span>
              </div>

              {/* Interface Properties */}
              <div className="space-y-2 text-xs py-3 border-y border-slate-800/80 mb-4">
                <div className="flex justify-between">
                  <span className="text-slate-400">Assigned IPv4:</span>
                  <span className="font-mono text-slate-200 font-semibold">{iface.ip}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Subnet Mask:</span>
                  <span className="font-mono text-slate-300">{iface.netmask}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Subnet CIDR:</span>
                  <span className="font-mono text-blue-400 font-semibold">{iface.network}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Default Gateway:</span>
                  <span className="font-mono text-indigo-300 font-semibold">
                    {iface.gateway || 'None'}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between">
                <button
                  onClick={() => onSelectInterface(iface.name)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
                  }`}
                >
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                  {isSelected ? 'Active Target' : 'Select Target'}
                </button>

                <button
                  onClick={() => {
                    onSelectInterface(iface.name);
                    onNavigate('discovery');
                  }}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium transition-colors"
                >
                  Scan this Subnet
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

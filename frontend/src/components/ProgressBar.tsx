import React from 'react';
import { XCircle, Loader2 } from 'lucide-react';

interface ProgressBarProps {
  progress: number;
  currentStep: string;
  isScanning: boolean;
  onCancel?: () => void;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  currentStep,
  isScanning,
  onCancel,
}) => {
  if (!isScanning && progress === 0) return null;

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 shadow-xl backdrop-blur-sm animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isScanning && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
          <span className="text-xs font-semibold text-slate-200">{currentStep}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-blue-400">{progress}%</span>
          {isScanning && onCancel && (
            <button
              onClick={onCancel}
              className="text-slate-400 hover:text-red-400 text-xs flex items-center gap-1 transition-colors px-2 py-0.5 rounded bg-slate-900 border border-slate-700"
            >
              <XCircle className="w-3.5 h-3.5" />
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-400 rounded-full transition-all duration-300 shadow-sm shadow-blue-500/50"
          style={{ width: `${Math.max(3, Math.min(100, progress))}%` }}
        />
      </div>
    </div>
  );
};

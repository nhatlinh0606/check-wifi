import React, { useState } from 'react';
import { History, FileText, Download, X, Eye, Calendar, RefreshCw, Compass } from 'lucide-react';
import { ScanHistoryItem } from '../types';
import { fetchScanReport, fetchHistoricalReport } from '../services/api';

interface HistoryPageProps {
  history: ScanHistoryItem[];
  onRefreshHistory: () => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ history, onRefreshHistory }) => {
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  const handleViewReport = async (item: ScanHistoryItem) => {
    setIsLoadingReport(true);
    try {
      let data: any;
      if (item.filename.startsWith('diagnosis_')) {
        data = await fetchHistoricalReport(item.filename);
      } else {
        data = await fetchScanReport(item.id || item.filename);
      }
      setSelectedReport(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingReport(false);
    }
  };

  const handleDownloadJson = (data: any, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-blue-400" />
            Diagnostic Scan & Recovery History
          </h2>
          <p className="text-xs text-slate-400">
            Archived autonomous diagnosis reports and structured network telemetry JSON
          </p>
        </div>
        <button
          onClick={onRefreshHistory}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 text-blue-400" />
          Refresh History
        </button>
      </div>

      {history.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
          <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-300">No diagnosis history recorded yet</h4>
          <p className="text-xs text-slate-500 mt-1">
            Run an Automatic Diagnosis from the Dashboard to generate and persist reports.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {history.map((item, idx) => (
            <div
              key={item.id || idx}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                    <Calendar className="w-3.5 h-3.5 text-blue-400" />
                    {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Recent Diagnosis'}
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                    {item.filename}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  {item.scenario_id && (
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold">
                      {item.scenario_id.toUpperCase()}
                    </span>
                  )}
                  {item.confidence_rating && (
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                      {item.confidence_rating}
                    </span>
                  )}
                </div>
              </div>

              {item.scenario_title && (
                <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-amber-400" />
                  <span>{item.scenario_title}</span>
                </div>
              )}

              <div className="text-xs py-2 border-y border-slate-800/80 flex items-center justify-between text-slate-400 font-mono">
                <div>
                  Gateway: <span className="text-emerald-400">{item.gateway_ip || item.gateway || 'N/A'}</span>
                </div>
                <div>
                  File Size: <span className="text-slate-300">{item.file_size ? `${item.file_size} B` : 'JSON'}</span>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={() => handleViewReport(item)}
                  disabled={isLoadingReport}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <Eye className="w-3.5 h-3.5" />
                  View JSON
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* JSON Viewer Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-4xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-white text-sm">Diagnosis Telemetry Viewer</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadJson(selectedReport, 'diagnosis_report.json')}
                  className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white flex items-center gap-1.5 cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON
                </button>
                <button
                  onClick={() => setSelectedReport(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-4 overflow-auto bg-slate-950/80 font-mono text-xs text-slate-300">
              <pre>{JSON.stringify(selectedReport, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

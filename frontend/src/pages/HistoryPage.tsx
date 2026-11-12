import React, { useState } from 'react';
import { History, FileText, Download, X, Eye, Calendar, RefreshCw } from 'lucide-react';
import { ScanHistoryItem } from '../types';
import { fetchScanReport } from '../services/api';

interface HistoryPageProps {
  history: ScanHistoryItem[];
  onRefreshHistory: () => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ history, onRefreshHistory }) => {
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  const handleViewReport = async (reportId: string) => {
    setIsLoadingReport(true);
    try {
      const data = await fetchScanReport(reportId);
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
            Diagnostic Scan History
          </h2>
          <p className="text-xs text-slate-400">
            Archived discovery reports saved in structured JSON telemetry format
          </p>
        </div>
        <button
          onClick={onRefreshHistory}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 text-blue-400" />
          Refresh History
        </button>
      </div>

      {history.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
          <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-300">No scan history recorded yet</h4>
          <p className="text-xs text-slate-500 mt-1">
            Complete a discovery scan to generate and persist reports in the reports directory.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {history.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                    <Calendar className="w-3.5 h-3.5 text-blue-400" />
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                    {item.filename}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    {item.results_count} Hosts
                  </span>
                  {item.tplink_count > 0 && (
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.tplink_count} TP-Link
                    </span>
                  )}
                </div>
              </div>

              <div className="text-xs py-2 border-y border-slate-800/80 flex items-center justify-between text-slate-400 font-mono">
                <div>
                  Iface: <span className="text-slate-200">{item.interface || 'N/A'}</span>
                </div>
                <div>
                  Subnet: <span className="text-blue-400">{item.subnet || 'N/A'}</span>
                </div>
                <div>
                  GW: <span className="text-indigo-300">{item.gateway || 'N/A'}</span>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={() => handleViewReport(item.id)}
                  disabled={isLoadingReport}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
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
                <h3 className="font-bold text-white text-sm">Scan Report Viewer</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadJson(selectedReport, 'report.json')}
                  className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </button>
                <button
                  onClick={() => setSelectedReport(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
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

import React, { useState } from 'react';
import {
  FileKey,
  Upload,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Copy,
  Check,
  ShieldCheck,
  FolderOpen,
  FileText,
} from 'lucide-react';
import { FullDiagnosisResult, CredentialSourceAudit } from '../types';
import { importBackupFile } from '../services/api';

interface CredentialRecoveryPageProps {
  latestDiagnosis: FullDiagnosisResult | null;
}

export const CredentialRecoveryPage: React.FC<CredentialRecoveryPageProps> = ({
  latestDiagnosis,
}) => {
  const [revealedSecrets, setRevealedSecrets] = useState<Record<string, boolean>>({});
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const credData = latestDiagnosis?.credentials;
  const sources: CredentialSourceAudit[] = credData?.sources || [];

  const toggleReveal = (id: string) => {
    setRevealedSecrets((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      const res = await importBackupFile(file);
      setUploadResult(res);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to analyze backup file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Information Header & Limitation Alert */}
      <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-500/5 flex items-start gap-3 text-xs text-slate-300">
        <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Authorized Local Credential Audit: </span>
          The system queries legitimate local configuration stores on this Ubuntu machine (such as active NetworkManager
          profiles and existing router backup archives). Passive Wi-Fi beacon inspection does not contain PSK credentials.
          If credentials are not found in local stores and you do not have physical access, connecting an Ethernet cable or
          performing an official router hardware reset is required.
        </div>
      </div>

      {/* Credential Sources Audit Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <FileKey className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Authorized Credential Sources Status
              </h3>
              <p className="text-xs text-slate-400">
                Audited local stores: NetworkManager, system keyfiles, backup files, and documents
              </p>
            </div>
          </div>

          <div className="text-xs">
            Overall Matching Credentials:{' '}
            <span
              className={`font-bold font-mono ${
                credData?.matching_credential_found ? 'text-emerald-400' : 'text-slate-400'
              }`}
            >
              {credData?.matching_credential_found ? 'FOUND' : 'NOT FOUND IN LOCAL STORES'}
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4">Recovery Source</th>
                <th className="py-3 px-4">Source Type</th>
                <th className="py-3 px-4">Audit Status</th>
                <th className="py-3 px-4">Credentials Discovered</th>
                <th className="py-3 px-4">Technical Explanation / Limitations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {sources.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No credential audit results available. Run Automatic Diagnosis to audit local sources.
                  </td>
                </tr>
              ) : (
                sources.map((src, idx) => {
                  const isFound = src.status === 'Found' || src.matching_credential_found;
                  const isPermReq = src.status === 'Permission required';

                  return (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-white">
                        <div className="flex items-center gap-2">
                          <FolderOpen className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                          <span>{src.source_name}</span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                          {src.source_type}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                            isFound
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : isPermReq
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {isFound ? (
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          ) : isPermReq ? (
                            <AlertCircle className="w-3 h-3 text-amber-400" />
                          ) : (
                            <XCircle className="w-3 h-3 text-slate-500" />
                          )}
                          {src.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        {src.credentials?.length > 0 ? (
                          <div className="space-y-2">
                            {src.credentials.map((c, cidx) => {
                              const credId = `${idx}-${cidx}`;
                              const isRevealed = revealedSecrets[credId] || false;
                              const secret = c.secret || '';

                              return (
                                <div key={cidx} className="p-2 rounded bg-slate-950 border border-slate-800 space-y-1">
                                  <div className="flex items-center justify-between text-[11px]">
                                    <span className="font-semibold text-white">{c.ssid || c.identity || 'Saved Key'}</span>
                                    <span className="text-slate-500 font-mono">{c.encryption_type || 'WPA2-PSK'}</span>
                                  </div>

                                  <div className="flex items-center justify-between gap-2 pt-1">
                                    <span className="font-mono text-emerald-400 bg-slate-900 px-2 py-0.5 rounded text-[11px]">
                                      {isRevealed ? secret : '••••••••••••'}
                                    </span>
                                    <div className="flex items-center gap-1">
                                      <button
                                        onClick={() => toggleReveal(credId)}
                                        className="p-1 text-slate-400 hover:text-white rounded"
                                        title={isRevealed ? 'Hide' : 'Reveal'}
                                      >
                                        {isRevealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                      </button>
                                      <button
                                        onClick={() => copyToClipboard(secret, credId)}
                                        className="p-1 text-slate-400 hover:text-white rounded"
                                        title="Copy Password"
                                      >
                                        {copiedKey === credId ? (
                                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                                        ) : (
                                          <Copy className="w-3.5 h-3.5" />
                                        )}
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <span className="text-slate-500 italic">No credentials found</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 text-[11px] leading-relaxed max-w-xs">
                        {src.technical_limitation_note || src.description}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload & Analyze Router Backup File */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-2.5">
          <Upload className="w-5 h-5 text-blue-400" />
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Import & Audit Router Backup File (.bin, .conf, .xml, .txt)
            </h3>
            <p className="text-xs text-slate-400">
              Upload a previously exported router backup file from your PC to recover configuration settings and credentials offline.
            </p>
          </div>
        </div>

        <div className="p-6 border-2 border-dashed border-slate-800 rounded-xl bg-slate-950/40 text-center space-y-3">
          <FileText className="w-8 h-8 text-slate-500 mx-auto" />
          <div className="text-xs text-slate-300">
            Select a router backup or configuration export file to analyze locally:
          </div>
          <div>
            <label className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all cursor-pointer shadow-md shadow-blue-600/20">
              <Upload className="w-4 h-4" />
              {isUploading ? 'Analyzing File...' : 'Choose File to Analyze'}
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={isUploading}
                accept=".bin,.conf,.xml,.txt,.tar.gz,.gz,.json"
                className="hidden"
              />
            </label>
          </div>
          <div className="text-[11px] text-slate-500">
            Supports TP-Link rom-0, config.bin, backup.conf, and standard XML/plaintext router configurations.
          </div>
        </div>

        {uploadError && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {uploadResult && (
          <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Backup Analyzed: {uploadResult.filename} ({uploadResult.bytes_analyzed} bytes)</span>
            </div>

            {uploadResult.credentials_found?.length > 0 ? (
              <div className="text-xs text-slate-300 space-y-2 pt-2">
                <div className="font-semibold text-white">Discovered Credentials:</div>
                {uploadResult.credentials_found.map((c: any, i: number) => (
                  <div key={i} className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono">
                    {JSON.stringify(c, null, 2)}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400">
                File parsed successfully. No plaintext passwords or known obfuscation patterns identified in this backup file.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

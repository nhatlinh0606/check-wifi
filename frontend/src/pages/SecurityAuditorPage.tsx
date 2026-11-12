import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  KeyRound,
  FileText,
  Clock,
  Sparkles,
  Copy,
  Check,
  AlertTriangle,
  Info,
  CheckCircle2,
  RefreshCw,
  Upload,
  Gauge,
} from 'lucide-react';
import {
  PasswordEvaluation,
  WordlistAnalysisResult,
  SearchSpaceSimulation,
} from '../types';
import {
  analyzePassword,
  generatePassword,
  analyzeWordlistFile,
  analyzeWordlistText,
  simulateSearchSpace,
} from '../services/api';

export const SecurityAuditorPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'analyzer' | 'generator' | 'wordlist' | 'simulator'>('analyzer');

  // Tab 1: Password Analyzer State
  const [testPassword, setTestPassword] = useState('MyWifiPass2026!');
  const [analysis, setAnalysis] = useState<PasswordEvaluation | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Tab 2: Generator State
  const [genLength, setGenLength] = useState(16);
  const [includeUpper, setIncludeUpper] = useState(true);
  const [includeLower, setIncludeLower] = useState(true);
  const [includeDigits, setIncludeDigits] = useState(true);
  const [includeSymbols, setIncludeSymbols] = useState(true);
  const [excludeAmbiguous, setExcludeAmbiguous] = useState(true);
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [genAnalysis, setGenAnalysis] = useState<PasswordEvaluation | null>(null);
  const [copiedGen, setCopiedGen] = useState(false);

  // Tab 3: Wordlist Analyzer State
  const [wordlistText, setWordlistText] = useState('12345678\npassword\nadmin123\n12345678\nMyWifi2026!\n0943561541');
  const [wordlistResult, setWordlistResult] = useState<WordlistAnalysisResult | null>(null);
  const [isAnalyzingWordlist, setIsAnalyzingWordlist] = useState(false);

  // Tab 4: Simulator State
  const [simCharset, setSimCharset] = useState('numeric');
  const [simLength, setSimLength] = useState(8);
  const [simAttempts, setSimAttempts] = useState(1000);
  const [simResult, setSimResult] = useState<SearchSpaceSimulation | null>(null);

  // Initial trigger for password analysis
  useEffect(() => {
    handleRunAnalysis(testPassword);
    handleGenerateNewPassword();
    handleRunSimulation('numeric', 8, 1000);
  }, []);

  const handleRunAnalysis = async (pwd: string) => {
    if (!pwd) {
      setAnalysis(null);
      return;
    }
    setIsAnalyzing(true);
    try {
      const res = await analyzePassword(pwd);
      setAnalysis(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateNewPassword = async () => {
    try {
      const res = await generatePassword({
        length: genLength,
        include_upper: includeUpper,
        include_lower: includeLower,
        include_digits: includeDigits,
        include_symbols: includeSymbols,
        exclude_ambiguous: excludeAmbiguous,
      });
      setGeneratedPassword(res.password);
      setGenAnalysis(res.analysis);
      setCopiedGen(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAnalyzeWordlist = async () => {
    setIsAnalyzingWordlist(true);
    try {
      const res = await analyzeWordlistText(wordlistText);
      setWordlistResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzingWordlist(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsAnalyzingWordlist(true);
    try {
      const res = await analyzeWordlistFile(file);
      setWordlistResult(res);
    } catch (err: any) {
      alert(err.message || 'Failed to analyze wordlist file');
    } finally {
      setIsAnalyzingWordlist(false);
    }
  };

  const handleRunSimulation = async (charset: string, len: number, atts: number) => {
    try {
      const res = await simulateSearchSpace({
        charset_type: charset,
        length: len,
        attempts_per_sec: atts,
      });
      setSimResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  const copyToClipboard = (text: string, setCopied: (v: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStrengthBarWidth = (strength?: string) => {
    switch (strength) {
      case 'Very Strong': return '100%';
      case 'Strong': return '80%';
      case 'Fair': return '60%';
      case 'Weak': return '40%';
      default: return '20%';
    }
  };

  const getStrengthBarColor = (strength?: string) => {
    switch (strength) {
      case 'Very Strong': return 'bg-emerald-500';
      case 'Strong': return 'bg-blue-500';
      case 'Fair': return 'bg-yellow-500';
      case 'Weak': return 'bg-amber-500';
      default: return 'bg-rose-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900/50 via-indigo-900/40 to-slate-900/80 border border-blue-500/30">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Wi-Fi Password Security Auditor & Hardening Suite
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium">
                Offline & Safe
              </span>
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Audit Wi-Fi password strength, detect weak human patterns, generate cryptographically secure
              WPA2/WPA3 keys, analyze wordlist quality, and simulate theoretical search spaces mathematically.
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <button
          onClick={() => setActiveTab('analyzer')}
          className={`p-3.5 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
            activeTab === 'analyzer'
              ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-600/25'
              : 'bg-slate-900/70 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Gauge className="w-4 h-4 shrink-0" />
          <div>
            <div className="font-bold text-xs uppercase tracking-wider">Strength Meter</div>
            <div className="text-[11px] opacity-80">Entropy & Patterns</div>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('generator')}
          className={`p-3.5 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
            activeTab === 'generator'
              ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-600/25'
              : 'bg-slate-900/70 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <KeyRound className="w-4 h-4 shrink-0" />
          <div>
            <div className="font-bold text-xs uppercase tracking-wider">WPA Key Generator</div>
            <div className="text-[11px] opacity-80">WPA2/WPA3 Random</div>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('wordlist')}
          className={`p-3.5 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
            activeTab === 'wordlist'
              ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-600/25'
              : 'bg-slate-900/70 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4 shrink-0" />
          <div>
            <div className="font-bold text-xs uppercase tracking-wider">Wordlist Quality</div>
            <div className="text-[11px] opacity-80">Duplicates & Redundancy</div>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('simulator')}
          className={`p-3.5 rounded-xl border text-left transition-all flex items-center gap-2.5 ${
            activeTab === 'simulator'
              ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-600/25'
              : 'bg-slate-900/70 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
          }`}
        >
          <Clock className="w-4 h-4 shrink-0" />
          <div>
            <div className="font-bold text-xs uppercase tracking-wider">Pattern Simulator</div>
            <div className="text-[11px] opacity-80">Math & Search Space</div>
          </div>
        </button>
      </div>

      {/* Tab 1: Password Strength & Entropy Analyzer */}
      {activeTab === 'analyzer' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-5">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Gauge className="w-4 h-4 text-blue-400" />
                Interactive Wi-Fi Password Security Evaluator
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Test any prospective Wi-Fi key offline to measure mathematical entropy and vulnerability
              </p>
            </div>

            {/* Input Box */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-medium text-slate-300">
                  Input Password to Audit
                </label>
                {isAnalyzing && (
                  <span className="text-[10px] text-blue-400 flex items-center gap-1 font-mono">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Evaluating...
                  </span>
                )}
              </div>
              <input
                type="text"
                value={testPassword}
                onChange={(e) => {
                  setTestPassword(e.target.value);
                  handleRunAnalysis(e.target.value);
                }}
                placeholder="Enter password..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            {/* Analysis Results Display */}
            {analysis && (
              <div className="space-y-5 pt-2">
                {/* Visual Strength Meter */}
                <div>
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-slate-400">Security Rating:</span>
                    <span className="font-bold text-slate-200 flex items-center gap-1.5">
                      {analysis.strength}
                      <span className="text-slate-500">({analysis.entropy_bits} bits entropy)</span>
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${getStrengthBarColor(analysis.strength)}`}
                      style={{ width: getStrengthBarWidth(analysis.strength) }}
                    />
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400 mb-0.5">Length</div>
                    <div className="font-mono font-bold text-base text-white">{analysis.length} chars</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400 mb-0.5">Entropy</div>
                    <div className="font-mono font-bold text-base text-blue-400">{analysis.entropy_bits} bits</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400 mb-0.5">Key Space</div>
                    <div className="font-mono font-bold text-base text-indigo-400 truncate">
                      {analysis.theoretical_combinations}
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400 mb-0.5">Char Sets</div>
                    <div className="font-mono text-xs font-semibold text-emerald-400 flex justify-center gap-1 mt-1">
                      {analysis.character_sets.lowercase && <span title="lowercase">a-z</span>}
                      {analysis.character_sets.uppercase && <span title="uppercase">A-Z</span>}
                      {analysis.character_sets.digits && <span title="digits">0-9</span>}
                      {analysis.character_sets.symbols && <span title="symbols">#&!</span>}
                    </div>
                  </div>
                </div>

                {/* Weak Pattern Warnings */}
                {analysis.warnings.length > 0 && (
                  <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 space-y-2 text-xs">
                    <div className="font-bold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                      <AlertTriangle className="w-4 h-4" />
                      Detected Vulnerability Patterns:
                    </div>
                    {analysis.warnings.map((w, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-slate-300">
                        <span className="text-amber-400">•</span>
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Crack Time Estimates Across Attack Profiles */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                    Theoretical Exhaustion Duration (By Attack Scenario)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400">Online Rate-Limited (5/s):</div>
                      <div className="font-bold text-emerald-400 font-mono">
                        {analysis.crack_time_estimates.online_router_5_per_sec}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400">Offline CPU (10,000/s):</div>
                      <div className="font-bold text-yellow-400 font-mono">
                        {analysis.crack_time_estimates.offline_cpu_10k_per_sec}
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <div className="text-slate-400">Offline GPU Rig (1M/s):</div>
                      <div className="font-bold text-blue-400 font-mono">
                        {analysis.crack_time_estimates.offline_gpu_1m_per_sec}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-900/40 space-y-1.5 text-xs text-slate-300">
                  <div className="font-semibold text-blue-300 flex items-center gap-1.5 mb-1">
                    <Info className="w-4 h-4 text-blue-400" />
                    Security Hardening Advice:
                  </div>
                  {analysis.recommendations.map((r, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: WPA2/WPA3 Password Generator */}
      {activeTab === 'generator' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-6">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400" />
                Strong WPA2 / WPA3 Wi-Fi Password Generator
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Generate high-entropy cryptographically randomized passwords compatible with all wireless routers
              </p>
            </div>

            {/* Generated Password Box */}
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Generated WPA Pre-Shared Key:</span>
                <span className="font-mono text-emerald-400 font-semibold">
                  {genAnalysis?.entropy_bits || 0} bits entropy
                </span>
              </div>

              <div className="font-mono font-bold text-lg text-white select-all break-all py-1 tracking-wider">
                {generatedPassword || 'Generating...'}
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => copyToClipboard(generatedPassword, setCopiedGen)}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-md shadow-blue-600/30"
                >
                  {copiedGen ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
                  {copiedGen ? 'Password Copied to Clipboard!' : 'Copy Generated Password'}
                </button>

                <button
                  onClick={handleGenerateNewPassword}
                  className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
                  title="Regenerate"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-4 pt-2 border-t border-slate-800">
              <div>
                <div className="flex justify-between items-center text-xs font-medium text-slate-300 mb-2">
                  <span>Password Length:</span>
                  <span className="font-mono text-blue-400 font-bold">{genLength} characters</span>
                </div>
                <input
                  type="range"
                  min="8"
                  max="63"
                  value={genLength}
                  onChange={(e) => setGenLength(parseInt(e.target.value))}
                  className="w-full accent-blue-500 bg-slate-950 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>8 chars (WPA min)</span>
                  <span>16 chars (Recommended)</span>
                  <span>32 chars</span>
                  <span>63 chars (WPA max)</span>
                </div>
              </div>

              {/* Character Set Toggles */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={includeUpper}
                    onChange={(e) => setIncludeUpper(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                  />
                  <span>Uppercase (A-Z)</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={includeLower}
                    onChange={(e) => setIncludeLower(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                  />
                  <span>Lowercase (a-z)</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={includeDigits}
                    onChange={(e) => setIncludeDigits(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                  />
                  <span>Numbers (0-9)</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={includeSymbols}
                    onChange={(e) => setIncludeSymbols(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                  />
                  <span>Special Symbols (!@#$)</span>
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={excludeAmbiguous}
                    onChange={(e) => setExcludeAmbiguous(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                  />
                  <span>Exclude Ambiguous (l, 1, O, 0)</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Wordlist Quality Analyzer */}
      {activeTab === 'wordlist' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-5">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                Password Wordlist Quality & Redundancy Auditor
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Analyze password dictionary files (up to 1,000,000 entries) to detect duplicates, sequential patterns, and weak entries
              </p>
            </div>

            {/* Upload or Paste */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-xs font-medium text-slate-300">
                  Option A: Upload Wordlist TXT File
                </label>
                <div className="border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-950/40">
                  <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                  <div className="text-xs text-slate-300 font-medium">Select a .txt wordlist file</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Supports plain text line-by-line dictionary files</div>
                  <input
                    type="file"
                    accept=".txt,.lst,.wordlist"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="wordlist-upload"
                  />
                  <label
                    htmlFor="wordlist-upload"
                    className="mt-3 inline-block px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 cursor-pointer"
                  >
                    Browse Files
                  </label>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-medium text-slate-300">
                  Option B: Paste Sample Wordlist Text
                </label>
                <textarea
                  rows={5}
                  value={wordlistText}
                  onChange={(e) => setWordlistText(e.target.value)}
                  placeholder="Paste passwords line by line..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleAnalyzeWordlist}
                  disabled={isAnalyzingWordlist}
                  className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-blue-600/30"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzingWordlist ? 'animate-spin' : ''}`} />
                  {isAnalyzingWordlist ? 'Analyzing Entries...' : 'Analyze Pasted Text'}
                </button>
              </div>
            </div>

            {/* Wordlist Analysis Results */}
            {wordlistResult && (
              <div className="pt-4 border-t border-slate-800 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400">Total Entries</div>
                    <div className="font-mono font-bold text-lg text-white">
                      {wordlistResult.total_entries.toLocaleString()}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400">Unique Entries</div>
                    <div className="font-mono font-bold text-lg text-emerald-400">
                      {wordlistResult.unique_entries.toLocaleString()}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400">Duplicate Rate</div>
                    <div className="font-mono font-bold text-lg text-amber-400">
                      {wordlistResult.duplicate_rate_pct}%
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      ({wordlistResult.duplicate_count} dupes)
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[11px] text-slate-400">Quality Grade</div>
                    <div className="font-mono font-bold text-sm text-blue-300 mt-1">
                      {wordlistResult.quality_grade}
                    </div>
                  </div>
                </div>

                {/* Additional metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400">Avg / Min / Max Length:</span>
                    <div className="font-mono font-semibold text-slate-200 mt-0.5">
                      {wordlistResult.avg_length} / {wordlistResult.min_length} / {wordlistResult.max_length}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400">Pure Numeric Passwords:</span>
                    <div className="font-mono font-semibold text-amber-300 mt-0.5">
                      {wordlistResult.pure_numeric_count} ({wordlistResult.pure_numeric_pct}%)
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400">Sequential Numeric Sequences:</span>
                    <div className="font-mono font-semibold text-rose-300 mt-0.5">
                      {wordlistResult.sequential_count} found
                    </div>
                  </div>
                </div>

                {/* Sample weak entries */}
                {wordlistResult.sample_weak_entries.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Sample Low-Entropy / Weak Entries in Wordlist:
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      {wordlistResult.sample_weak_entries.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex justify-between items-center"
                        >
                          <span className="font-mono text-slate-200 font-semibold">{item.entry}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            {item.reason}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Brute-force Pattern Simulator */}
      {activeTab === 'simulator' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-6">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" />
                Offline Educational Search-Space & Exhaustion Simulator
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Calculate theoretical key space sizes ($N^L$) and estimated search durations mathematically.
                Never connects to Wi-Fi networks or transmits authentication attempts.
              </p>
            </div>

            {/* Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Character Set Alphabet
                </label>
                <select
                  value={simCharset}
                  onChange={(e) => {
                    setSimCharset(e.target.value);
                    handleRunSimulation(e.target.value, simLength, simAttempts);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                >
                  <option value="numeric">Numeric (0-9) - 10 chars</option>
                  <option value="alpha_lower">Lowercase (a-z) - 26 chars</option>
                  <option value="alpha_mixed">Mixed Letters (a-z, A-Z) - 52 chars</option>
                  <option value="alphanumeric">Alphanumeric (Letters + Digits) - 62 chars</option>
                  <option value="ascii_printable">Full ASCII Printable + Symbols - 95 chars</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs font-medium text-slate-300 mb-1.5">
                  <span>Password Length:</span>
                  <span className="font-mono text-blue-400 font-bold">{simLength} chars</span>
                </div>
                <input
                  type="range"
                  min="4"
                  max="24"
                  value={simLength}
                  onChange={(e) => {
                    const l = parseInt(e.target.value);
                    setSimLength(l);
                    handleRunSimulation(simCharset, l, simAttempts);
                  }}
                  className="w-full accent-blue-500 bg-slate-950 cursor-pointer mt-2"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Simulated Speed (Attempts / sec)
                </label>
                <select
                  value={simAttempts}
                  onChange={(e) => {
                    const atts = parseFloat(e.target.value);
                    setSimAttempts(atts);
                    handleRunSimulation(simCharset, simLength, atts);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                >
                  <option value="5">5 att/s (Online Web Portal / Router)</option>
                  <option value="1000">1,000 att/s (Low-end Single Thread)</option>
                  <option value="50000">50,000 att/s (Multi-core Desktop CPU)</option>
                  <option value="1000000">1,000,000 att/s (High-end GPU)</option>
                  <option value="100000000">100,000,000 att/s (Enterprise Hash Cluster)</option>
                </select>
              </div>
            </div>

            {/* Simulation Results Display */}
            {simResult && (
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">Alphabet Pool ($N$)</div>
                    <div className="font-mono font-bold text-lg text-white">
                      {simResult.pool_size} chars
                    </div>
                    <div className="text-[11px] text-slate-500 truncate">{simResult.charset_label}</div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">Search Space ($N^L$)</div>
                    <div className="font-mono font-bold text-lg text-blue-400 truncate">
                      {simResult.total_combinations_scientific}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono">
                      {simResult.total_combinations_exact}
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">Avg Search Time (50%)</div>
                    <div className="font-mono font-bold text-lg text-emerald-400 truncate">
                      {simResult.time_to_exhaust_average_50pct}
                    </div>
                    <div className="text-[11px] text-slate-500">at {simResult.attempts_per_sec.toLocaleString()} att/s</div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-xs text-slate-400 mb-1">Worst-case (100%)</div>
                    <div className="font-mono font-bold text-lg text-amber-400 truncate">
                      {simResult.time_to_exhaust_worst_case}
                    </div>
                    <div className="text-[11px] text-slate-500">Full key space sweep</div>
                  </div>
                </div>

                {/* Educational Takeaway */}
                <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-900/40 text-xs text-slate-300 space-y-1">
                  <div className="font-semibold text-blue-300 flex items-center gap-1.5">
                    <Info className="w-4 h-4 text-blue-400" />
                    Mathematical Observation:
                  </div>
                  <p>
                    Notice how changing the alphabet from <strong>Numeric (10)</strong> to <strong>Alphanumeric (62)</strong> multiplies
                    the search space exponentially: an 8-character numeric pin has only <strong>100 million</strong> combinations,
                    whereas an 8-character alphanumeric key has <strong>218 trillion</strong> combinations!
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

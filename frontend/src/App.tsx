import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { NetworkDiscoveryPage } from './pages/NetworkDiscoveryPage';
import { RouterIdentificationPage } from './pages/RouterIdentificationPage';
import { CredentialRecoveryPage } from './pages/CredentialRecoveryPage';
import { RecoveryPlanPage } from './pages/RecoveryPlanPage';
import { HistoryPage } from './pages/HistoryPage';
import { SecurityAuditorPage } from './pages/SecurityAuditorPage';
import { SettingsPage } from './pages/SettingsPage';
import {
  PageId,
  NetworkInterface,
  DiagnosisStatus,
  FullDiagnosisResult,
  ScanHistoryItem,
} from './types';
import {
  fetchInterfaces,
  fetchDiagnosisStatus,
  fetchLatestDiagnosis,
  fetchDiagnosisHistory,
  startDiagnosis,
  stopDiagnosis,
  fetchWifiNetworks,
} from './services/api';
import { wsClient } from './services/websocket';

const INITIAL_STAGES = [
  { id: 1, name: 'Detecting network interfaces & hardware controllers', status: 'pending' as const },
  { id: 2, name: 'Scanning wireless environment & radio signals', status: 'pending' as const },
  { id: 3, name: 'Analyzing Linux routing table, DNS & gateway', status: 'pending' as const },
  { id: 4, name: 'Discovering gateway devices & local hosts', status: 'pending' as const },
  { id: 5, name: 'Identifying router vendor & confidence rating', status: 'pending' as const },
  { id: 6, name: 'Checking router management web interfaces', status: 'pending' as const },
  { id: 7, name: 'Auditing local credential stores & backup files', status: 'pending' as const },
  { id: 8, name: 'Generating evidence-based recovery plan', status: 'pending' as const },
];

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string | null>(null);

  const [diagnosisStatus, setDiagnosisStatus] = useState<DiagnosisStatus>({
    status: 'idle',
    current_stage: 0,
    stage_message: 'Ready to start autonomous diagnosis',
    stages: INITIAL_STAGES,
    has_result: false,
  });

  const [latestDiagnosis, setLatestDiagnosis] = useState<FullDiagnosisResult | null>(null);
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load telemetry and saved reports
  const loadInitialData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [ifaces, statusData, latestResult, historyData] = await Promise.all([
        fetchInterfaces().catch(() => []),
        fetchDiagnosisStatus().catch(() => null),
        fetchLatestDiagnosis().catch(() => null),
        fetchDiagnosisHistory().catch(() => []),
      ]);

      setInterfaces(ifaces);
      if (ifaces.length > 0 && !selectedInterface) {
        const def = ifaces.find((i) => i.is_default) || ifaces[0];
        setSelectedInterface(def.name);
      }

      if (statusData) {
        setDiagnosisStatus(statusData);
      }
      if (latestResult) {
        setLatestDiagnosis(latestResult);
      }
      setHistory(historyData);
    } catch (e) {
      console.error('Error loading initial diagnosis data:', e);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedInterface]);

  // WebSocket Subscription for Real-time Stage Progress
  useEffect(() => {
    loadInitialData();
    wsClient.connect();

    const unsubscribe = wsClient.subscribe((event, data) => {
      if (event === 'diagnosis_start') {
        setDiagnosisStatus((prev) => ({
          ...prev,
          status: 'running',
          current_stage: 0,
          stage_message: 'Starting diagnosis...',
          stages: INITIAL_STAGES,
        }));
      } else if (event === 'diagnosis_progress') {
        setDiagnosisStatus((prev) => ({
          ...prev,
          current_stage: data.current_stage ?? prev.current_stage,
          stage_message: data.stage_message || prev.stage_message,
          stages: data.stages || prev.stages,
          status: data.status || prev.status,
        }));
      } else if (event === 'diagnosis_complete') {
        setDiagnosisStatus((prev) => ({
          ...prev,
          status: 'completed',
          stage_message: data.stage_message || 'Diagnosis complete',
        }));
        if (data.result) {
          setLatestDiagnosis(data.result);
        }
        fetchDiagnosisHistory().then(setHistory).catch(console.error);
      } else if (event === 'diagnosis_cancelled') {
        setDiagnosisStatus((prev) => ({
          ...prev,
          status: 'cancelled',
          stage_message: 'Diagnosis cancelled.',
        }));
      } else if (event === 'diagnosis_error') {
        setDiagnosisStatus((prev) => ({
          ...prev,
          status: 'failed',
          stage_message: data.stage_message || 'Diagnosis failed',
          error_message: data.error_message,
        }));
      }
    });

    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, [loadInitialData]);

  // Handle Starting Autonomous Diagnosis
  const handleStartDiagnosis = async () => {
    try {
      await startDiagnosis({
        target_interface: selectedInterface || undefined,
      });
      setCurrentPage('dashboard');
    } catch (err: any) {
      alert(err.message || 'Failed to start diagnosis');
    }
  };

  // Handle Stopping Diagnosis
  const handleStopDiagnosis = async () => {
    try {
      await stopDiagnosis();
    } catch (err: any) {
      console.error(err);
    }
  };

  // Handle Refreshing Wireless Airwaves
  const handleRefreshWifi = async () => {
    setIsRefreshing(true);
    try {
      const networks = await fetchWifiNetworks(true);
      if (latestDiagnosis) {
        setLatestDiagnosis({
          ...latestDiagnosis,
          wireless: {
            ...latestDiagnosis.wireless,
            networks,
            networks_count: networks.length,
            tplink_aps_detected: networks.filter((n) => n.is_tplink),
          },
        });
      }
    } catch (err) {
      console.error('Failed to rescan wifi:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const activeIface = interfaces.find((i) => i.name === selectedInterface) || interfaces[0] || null;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        activeInterface={activeIface}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header
          currentPage={currentPage}
          onQuickDiagnosis={handleStartDiagnosis}
          onStopDiagnosis={handleStopDiagnosis}
          isDiagnosing={diagnosisStatus.status === 'running'}
          onRefresh={loadInitialData}
          isRefreshing={isRefreshing}
        />

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto">
            {currentPage === 'dashboard' && (
              <DashboardPage
                diagnosisStatus={diagnosisStatus}
                latestDiagnosis={latestDiagnosis}
                onStartDiagnosis={handleStartDiagnosis}
                onStopDiagnosis={handleStopDiagnosis}
                onSelectPage={setCurrentPage}
              />
            )}

            {currentPage === 'network-discovery' && (
              <NetworkDiscoveryPage
                latestDiagnosis={latestDiagnosis}
                onRefreshWifi={handleRefreshWifi}
                isRefreshing={isRefreshing}
              />
            )}

            {currentPage === 'router-identification' && (
              <RouterIdentificationPage latestDiagnosis={latestDiagnosis} />
            )}

            {currentPage === 'credential-recovery' && (
              <CredentialRecoveryPage latestDiagnosis={latestDiagnosis} />
            )}

            {currentPage === 'recovery-plan' && (
              <RecoveryPlanPage latestDiagnosis={latestDiagnosis} />
            )}

            {currentPage === 'history' && (
              <HistoryPage
                history={history}
                onRefreshHistory={loadInitialData}
              />
            )}

            {currentPage === 'auditor' && <SecurityAuditorPage />}

            {currentPage === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};

import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { InspectModal } from './components/InspectModal';
import { WifiPasswordRecoveryPage } from './pages/WifiPasswordRecoveryPage';
import { DashboardPage } from './pages/DashboardPage';
import { InterfacesPage } from './pages/InterfacesPage';
import { WifiDiscoveryPage } from './pages/WifiDiscoveryPage';
import { RouterDiscoveryPage } from './pages/RouterDiscoveryPage';
import { HistoryPage } from './pages/HistoryPage';
import { RecoveryPage } from './pages/RecoveryPage';
import { SettingsPage } from './pages/SettingsPage';
import {
  PageId,
  NetworkInterface,
  WifiNetwork,
  DiscoveredDevice,
  ScanStatus,
  ScanHistoryItem,
  RecoveryCase,
} from './types';
import {
  fetchInterfaces,
  fetchWifiNetworks,
  fetchSavedWifiProfiles,
  fetchScanStatus,
  fetchScanHistory,
  fetchRecoveryCases,
  startDiscoveryScan,
  stopDiscoveryScan,
  inspectDevice,
} from './services/api';
import { wsClient } from './services/websocket';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('wifi-recovery');
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string | null>(null);
  const [wifiNetworks, setWifiNetworks] = useState<WifiNetwork[]>([]);
  const [savedProfiles, setSavedProfiles] = useState<Array<{ name: string; uuid: string; type: string; active: boolean }>>([]);
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const [scanStatus, setScanStatus] = useState<ScanStatus>({
    status: 'idle',
    progress: 0,
    current_step: 'Ready',
    discovered_devices: [],
    devices_count: 0,
    tplink_count: 0,
  });
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);
  const [recoveryCases, setRecoveryCases] = useState<Record<string, RecoveryCase>>({});
  const [inspectingDevice, setInspectingDevice] = useState<DiscoveredDevice | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [recoveryInitialCase, setRecoveryInitialCase] = useState<string>('A');

  // Load Wi-Fi networks
  const loadWifiNetworks = useCallback(async (rescan = false) => {
    try {
      setIsRefreshing(true);
      const nets = await fetchWifiNetworks(rescan);
      setWifiNetworks(nets);
    } catch (e) {
      console.error('Error loading Wi-Fi networks:', e);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Load initial metadata
  const loadInitialData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [ifaces, statusData, historyData, casesData, saved, nets] = await Promise.all([
        fetchInterfaces().catch(() => []),
        fetchScanStatus().catch(() => null),
        fetchScanHistory().catch(() => []),
        fetchRecoveryCases().catch(() => ({})),
        fetchSavedWifiProfiles().catch(() => []),
        fetchWifiNetworks(false).catch(() => []),
      ]);

      setInterfaces(ifaces);
      if (ifaces.length > 0 && !selectedInterface) {
        const def = ifaces.find((i) => i.is_default) || ifaces[0];
        setSelectedInterface(def.name);
      }

      if (statusData) {
        setScanStatus(statusData);
        if (statusData.discovered_devices?.length > 0) {
          setDevices(statusData.discovered_devices);
        }
      }

      setHistory(historyData);
      setRecoveryCases(casesData);
      setSavedProfiles(saved);
      if (nets?.length) {
        setWifiNetworks(nets);
      }
    } catch (e) {
      console.error('Error loading initial dashboard data:', e);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedInterface]);

  // WebSocket Subscription
  useEffect(() => {
    loadInitialData();
    wsClient.connect();

    const unsubscribe = wsClient.subscribe((event, data) => {
      if (event === 'scan_start' || event === 'scan_progress' || event === 'scan_complete' || event === 'scan_error') {
        setScanStatus((prev) => ({
          ...prev,
          status: data.status || prev.status,
          progress: data.progress ?? prev.progress,
          current_step: data.current_step || prev.current_step,
          discovered_devices: data.discovered_devices || prev.discovered_devices,
          devices_count: data.devices_count ?? prev.devices_count,
          tplink_count: data.tplink_count ?? prev.tplink_count,
        }));

        if (data.discovered_devices?.length) {
          setDevices(data.discovered_devices);
        }

        if (event === 'scan_complete') {
          fetchScanHistory().then(setHistory).catch(console.error);
        }
      } else if (event === 'device_found') {
        const found = data.device as DiscoveredDevice;
        if (found) {
          setDevices((prev) => {
            const exists = prev.some((d) => d.ip === found.ip);
            return exists ? prev.map((d) => (d.ip === found.ip ? found : d)) : [...prev, found];
          });
        }
        if (data.progress !== undefined) {
          setScanStatus((prev) => ({
            ...prev,
            progress: data.progress,
            current_step: data.current_step,
          }));
        }
      }
    });

    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, [loadInitialData]);

  // Handle Scan Start
  const handleStartScan = async (iface?: string, subnet?: string) => {
    try {
      setDevices([]);
      await startDiscoveryScan(iface || selectedInterface || undefined, subnet);
    } catch (err: any) {
      alert(err.message || 'Failed to start scan');
    }
  };

  // Handle Scan Cancel
  const handleCancelScan = async () => {
    try {
      await stopDiscoveryScan();
    } catch (err: any) {
      console.error(err);
    }
  };

  // Handle Inspect Device
  const handleInspectDevice = async (device: DiscoveredDevice) => {
    setInspectingDevice(device);
    try {
      const detailed = await inspectDevice(device.ip, device.mac || undefined);
      setInspectingDevice(detailed);
      setDevices((prev) => prev.map((d) => (d.ip === detailed.ip ? detailed : d)));
    } catch (e) {
      console.error('Deep inspect failed:', e);
    }
  };

  const handleNavigateToRecovery = (caseId: string) => {
    setRecoveryInitialCase(caseId);
    setCurrentPage('recovery');
  };

  const activeIface = interfaces.find((i) => i.name === selectedInterface) || interfaces[0] || null;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
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
          onQuickScan={() => handleStartScan()}
          isScanning={scanStatus.status === 'running'}
          onRefresh={() => {
            if (currentPage === 'wifi' || currentPage === 'wifi-recovery') loadWifiNetworks(true);
            else loadInitialData();
          }}
          isRefreshing={isRefreshing}
        />

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto">
            {currentPage === 'wifi-recovery' && (
              <WifiPasswordRecoveryPage
                networks={wifiNetworks}
                isScanning={isRefreshing}
                onRefreshNetworks={() => loadWifiNetworks(true)}
              />
            )}

            {currentPage === 'dashboard' && (
              <DashboardPage
                activeInterface={activeIface}
                scanStatus={scanStatus}
                devices={devices}
                onStartScan={handleStartScan}
                onCancelScan={handleCancelScan}
                onNavigate={setCurrentPage}
                onInspectDevice={handleInspectDevice}
              />
            )}

            {currentPage === 'interfaces' && (
              <InterfacesPage
                interfaces={interfaces}
                selectedInterface={selectedInterface}
                onSelectInterface={setSelectedInterface}
                onNavigate={setCurrentPage}
              />
            )}

            {currentPage === 'wifi' && (
              <WifiDiscoveryPage
                networks={wifiNetworks}
                savedProfiles={savedProfiles}
                isRefreshing={isRefreshing}
                onRefresh={loadWifiNetworks}
                onNavigate={setCurrentPage}
              />
            )}

            {currentPage === 'discovery' && (
              <RouterDiscoveryPage
                interfaces={interfaces}
                selectedInterface={selectedInterface}
                onSelectInterface={setSelectedInterface}
                scanStatus={scanStatus}
                devices={devices}
                onStartScan={handleStartScan}
                onCancelScan={handleCancelScan}
                onInspectDevice={handleInspectDevice}
              />
            )}

            {currentPage === 'history' && (
              <HistoryPage
                history={history}
                onRefreshHistory={loadInitialData}
              />
            )}

            {currentPage === 'recovery' && (
              <RecoveryPage
                cases={recoveryCases}
                initialCase={recoveryInitialCase}
              />
            )}

            {currentPage === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>

      {/* Device Inspect Modal */}
      <InspectModal
        device={inspectingDevice}
        onClose={() => setInspectingDevice(null)}
        onNavigateToRecovery={handleNavigateToRecovery}
      />
    </div>
  );
};

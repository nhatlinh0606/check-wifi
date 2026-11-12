import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { WifiRecoveryMainPage } from './pages/WifiRecoveryMainPage';
import { CredentialRecoveryPage } from './pages/CredentialRecoveryPage';
import { SecurityAuditorPage } from './pages/SecurityAuditorPage';
import { SettingsPage } from './pages/SettingsPage';
import { PageId, NetworkInterface } from './types';
import { fetchInterfaces } from './services/api';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('wifi-recovery');
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchInterfaces()
      .then(setInterfaces)
      .catch(console.error);
  }, []);

  const activeIface = interfaces.find((i) => i.is_default) || interfaces[0] || null;

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchInterfaces()
      .then(setInterfaces)
      .finally(() => setIsRefreshing(false));
  };

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
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {currentPage === 'wifi-recovery' && <WifiRecoveryMainPage />}

            {currentPage === 'credential-recovery' && (
              <CredentialRecoveryPage latestDiagnosis={null} />
            )}

            {currentPage === 'auditor' && <SecurityAuditorPage />}

            {currentPage === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};

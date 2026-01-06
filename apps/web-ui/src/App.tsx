import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/auth';
import { useThemeStore } from './stores/theme';
import { useEffect } from 'react';

// Layouts
import { MainLayout } from './components/layouts/MainLayout';
import { AuthLayout } from './components/layouts/AuthLayout';

// Auth pages
import { LoginPage } from './pages/auth/LoginPage';

// Dashboard
import { DashboardPage } from './pages/dashboard/DashboardPage';

// IPAM module
import { IPAMNetworksPage } from './modules/ipam/pages/NetworksPage';
import { IPAMNetworkDetailPage } from './modules/ipam/pages/NetworkDetailPage';

// NPM module
import { NPMDevicesPage } from './modules/npm/pages/DevicesPage';
import { NPMDeviceDetailPage } from './modules/npm/pages/DeviceDetailPage';
import { NPMAlertsPage } from './modules/npm/pages/AlertsPage';

// STIG module
import { STIGBenchmarksPage } from './modules/stig/pages/BenchmarksPage';
import { STIGAssetsPage } from './modules/stig/pages/AssetsPage';
import { STIGCompliancePage } from './modules/stig/pages/CompliancePage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  const { isDark } = useThemeStore();

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Routes>
        {/* Auth routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
        </Route>

        {/* Protected routes */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* IPAM Module */}
          <Route path="/ipam">
            <Route index element={<Navigate to="/ipam/networks" replace />} />
            <Route path="networks" element={<IPAMNetworksPage />} />
            <Route path="networks/:id" element={<IPAMNetworkDetailPage />} />
          </Route>

          {/* NPM Module */}
          <Route path="/npm">
            <Route index element={<Navigate to="/npm/devices" replace />} />
            <Route path="devices" element={<NPMDevicesPage />} />
            <Route path="devices/:id" element={<NPMDeviceDetailPage />} />
            <Route path="alerts" element={<NPMAlertsPage />} />
          </Route>

          {/* STIG Module */}
          <Route path="/stig">
            <Route index element={<Navigate to="/stig/benchmarks" replace />} />
            <Route path="benchmarks" element={<STIGBenchmarksPage />} />
            <Route path="assets" element={<STIGAssetsPage />} />
            <Route path="compliance" element={<STIGCompliancePage />} />
          </Route>
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </div>
  );
}

export default App;

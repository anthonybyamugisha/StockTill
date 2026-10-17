import { Route, Routes, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { useAuth } from './features/auth/hooks/useAuth';
import { AppLayout } from './app/layout/AppLayout';
import { LoginPage } from './features/auth/pages/LoginPage';
import { DashboardPage } from './features/dashboard/pages/DashboardPage';
import { POSPage } from './features/pos/pages/POSPage';
import { CatalogPage } from './features/catalog/pages/CatalogPage';
import { InventoryPage } from './features/inventory/pages/InventoryPage';
import { SalesPage } from './features/sales/pages/SalesPage';
import { ReportsPage } from './features/reports/pages/ReportsPage';
import { UsersPage } from './features/users/pages/UsersPage';
import { SettingsPage } from './features/settings/pages/SettingsPage';
import { AuditLogPage } from './features/audit/pages/AuditLogPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function Protected({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-surface-200 border-t-primary-500" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-surface-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-surface-200 border-t-primary-500" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/pos" element={<POSPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/sales" element={<SalesPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/audit-log" element={<AuditLogPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

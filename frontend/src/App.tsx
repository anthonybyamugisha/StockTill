import { Route, Routes, Navigate } from 'react-router-dom';
import { useAuth } from './features/auth/hooks/useAuth';
import { AppLayout } from './app/layout/AppLayout';
import { LoginPage } from './features/auth/pages/LoginPage';
import { ChangePasswordPage } from './features/auth/pages/ChangePasswordPage';
import { homePathFor } from './features/auth/lib/redirect';
import { DashboardPage } from './features/dashboard/pages/DashboardPage';
import { POSPage } from './features/pos/pages/POSPage';
import { CatalogPage } from './features/catalog/pages/CatalogPage';
import { InventoryPage } from './features/inventory/pages/InventoryPage';
import { PurchasingPage } from './features/purchasing/pages/PurchasingPage';
import { SalesPage } from './features/sales/pages/SalesPage';
import { ShiftsPage } from './features/shifts/pages/ShiftsPage';
import { ReportsPage } from './features/reports/pages/ReportsPage';
import { UsersPage } from './features/users/pages/UsersPage';
import { SettingsPage } from './features/settings/pages/SettingsPage';
import { AuditLogPage } from './features/audit/pages/AuditLogPage';
import { Toaster } from './shared/ui/Toaster';

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
  if (user.must_change_password) return <Navigate to="/change-password" replace />;
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
    <>
      <Toaster />
      <Routes>
        <Route path="/login" element={user ? <Navigate to={homePathFor(user)} replace /> : <LoginPage />} />
        <Route
          path="/change-password"
          element={!user ? <Navigate to="/login" replace /> : <ChangePasswordPage />}
        />
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
          <Route path="/purchasing" element={<PurchasingPage />} />
          <Route path="/sales" element={<SalesPage />} />
          <Route path="/shifts" element={<ShiftsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/audit-log" element={<AuditLogPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

function App() {
  return <AppRoutes />;
}

export default App;

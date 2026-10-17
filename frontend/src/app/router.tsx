import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { useAuth } from '../features/auth/hooks/useAuth';
import { ReactNode } from 'react';

function Protected({ children, roles }: { children: ReactNode; roles?: string[] }) {
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

export function AppRouter() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <Protected>
            <div>Already logged in</div>
          </Protected>
        }
      />
      <Route
        path="/auth/login"
        element={
          <LoginRedirect />
        }
      />
      <Route element={<Protected><AppLayout /></Protected>}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/pos" element={<POSPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/sales" element={<SalesPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/users" element={<UsersPage />} />
      </Route>
    </Routes>
  );
}

function LoginRedirect() {
  return <Navigate to="/login" replace />;
}

import { LoginPage } from '../features/auth/pages/LoginPage';
import { DashboardPage } from '../features/dashboard/pages/DashboardPage';
import { POSPage } from '../features/pos/pages/POSPage';
import { CatalogPage } from '../features/catalog/pages/CatalogPage';
import { InventoryPage } from '../features/inventory/pages/InventoryPage';
import { SalesPage } from '../features/sales/pages/SalesPage';
import { ReportsPage } from '../features/reports/pages/ReportsPage';
import { UsersPage } from '../features/users/pages/UsersPage';

function LoginGate() {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  if (user) return <Navigate to="/" replace />;
  return <LoginPage />;
}

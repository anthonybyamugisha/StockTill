import { ReactNode } from 'react';
import { Navigate, RouteObject } from 'react-router-dom';
import { useAuth } from '../features/auth/hooks/useAuth';

function Protected({ children, roles }: { children: ReactNode; roles?: string[] }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export const appRouter: ReactNode = (
  <>
    <Route path="/login" element={<div>Login Page</div>} />
    <Route
      path="/"
      element={
        <Protected>
          <div>Dashboard</div>
        </Protected>
      }
    />
    <Route
      path="/pos"
      element={
        <Protected>
          <div>POS</div>
        </Protected>
      }
    />
    <Route
      path="/catalog"
      element={
        <Protected>
          <div>Catalog</div>
        </Protected>
      }
    />
    <Route
      path="/inventory"
      element={
        <Protected>
          <div>Inventory</div>
        </Protected>
      }
    />
    <Route
      path="/sales"
      element={
        <Protected>
          <div>Sales</div>
        </Protected>
      }
    />
    <Route
      path="/reports"
      element={
        <Protected roles={['admin', 'manager']}>
          <div>Reports</div>
        </Protected>
      }
    />
    <Route
      path="/users"
      element={
        <Protected roles={['admin']}>
          <div>Users</div>
        </Protected>
      }
    />
  </>
);

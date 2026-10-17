import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { OfflineBanner } from './OfflineBanner';

export function AppLayout() {
  return (
    <div className="min-h-screen bg-surface-50">
      <Sidebar />
      <div className="ml-60">
        <Header />
        <OfflineBanner />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

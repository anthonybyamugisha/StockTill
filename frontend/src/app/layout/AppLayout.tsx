import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { OfflineBanner } from './OfflineBanner';

export function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface-50">
      <Sidebar isOpen={navOpen} onClose={() => setNavOpen(false)} />
      <div className="md:ml-20 lg:ml-60">
        <Header onOpenNav={() => setNavOpen(true)} />
        <OfflineBanner />
        <main className="p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

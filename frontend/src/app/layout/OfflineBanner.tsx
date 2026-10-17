import { useCallback, useEffect, useState } from 'react';
import { isOffline } from '../../features/pos/offline/networkError';
import { queuedSaleCount } from '../../features/pos/offline/saleQueue';
import { syncPendingSales } from '../../features/pos/offline/saleSync';
import { toast } from '../../shared/ui/toast';

export function OfflineBanner() {
  const [online, setOnline] = useState(!isOffline());
  const [pending, setPending] = useState(queuedSaleCount());
  const [syncing, setSyncing] = useState(false);

  const runSync = useCallback(async () => {
    setSyncing(true);
    try {
      const synced = await syncPendingSales();
      if (synced > 0) {
        toast.success(`${synced} offline sale${synced === 1 ? '' : 's'} synced`);
      }
    } finally {
      setPending(queuedSaleCount());
      setSyncing(false);
    }
  }, []);

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true);
      void runSync();
    };
    const handleOffline = () => {
      setOnline(false);
      setPending(queuedSaleCount());
    };
    const refresh = () => setPending(queuedSaleCount());

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('focus', refresh);
    void runSync();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('focus', refresh);
    };
  }, [runSync]);

  if (online && pending === 0) return null;

  const message = !online
    ? `Offline — sales are saved on this device${pending > 0 ? ` (${pending} waiting)` : ''}.`
    : `${pending} sale(s) waiting to sync.`;

  return (
    <div
      role="status"
      className="flex items-center justify-between gap-4 bg-amber-100 px-6 py-2 text-sm text-amber-900"
    >
      <span>{message}</span>
      {online && pending > 0 && (
        <button
          type="button"
          onClick={() => void runSync()}
          disabled={syncing}
          className="rounded border border-amber-400 bg-white px-3 py-1 text-xs font-medium text-amber-900 hover:bg-amber-50 disabled:opacity-60"
        >
          {syncing ? 'Syncing...' : 'Sync now'}
        </button>
      )}
    </div>
  );
}

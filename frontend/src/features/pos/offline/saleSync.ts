import { completeSale } from '../api/pos';
import { isOffline } from './networkError';
import { listQueuedSales, removeQueuedSale } from './saleQueue';

let syncing = false;

/**
 * Replays sales that were queued while offline. Because each sale carries its
 * idempotency key, a replay that the server already processed is harmless.
 */
export async function syncPendingSales(): Promise<number> {
  if (syncing || isOffline()) return 0;
  syncing = true;
  let synced = 0;
  try {
    for (const sale of listQueuedSales()) {
      try {
        await completeSale(sale.payload);
        removeQueuedSale(sale.id);
        synced += 1;
      } catch {
        break;
      }
    }
  } finally {
    syncing = false;
  }
  return synced;
}

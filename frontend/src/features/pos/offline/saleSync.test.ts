import { beforeEach, describe, expect, it, vi } from 'vitest';

const { completeSale } = vi.hoisted(() => ({ completeSale: vi.fn() }));

vi.mock('../api/pos', () => ({ completeSale }));

import type { CompleteSaleRequest } from '../api/pos';
import { queueSale, queuedSaleCount } from './saleQueue';
import { syncPendingSales } from './saleSync';

function makePayload(key: string): CompleteSaleRequest {
  return {
    lines: [{ product_id: 'p1', quantity: 1, unit_price: '1000.00', unit_cost: '500.00' }],
    payments: [{ method: 'cash', amount: '1000.00' }],
    idempotency_key: key,
  };
}

describe('syncPendingSales', () => {
  beforeEach(() => {
    localStorage.clear();
    completeSale.mockReset();
  });

  it('does nothing when the queue is empty', async () => {
    const synced = await syncPendingSales();
    expect(synced).toBe(0);
    expect(completeSale).not.toHaveBeenCalled();
  });

  it('sends queued sales and clears them on success', async () => {
    completeSale.mockResolvedValue({ receipt_number: 'R-1' });
    queueSale(makePayload('key-1'));
    queueSale(makePayload('key-2'));

    const synced = await syncPendingSales();

    expect(synced).toBe(2);
    expect(completeSale).toHaveBeenCalledTimes(2);
    expect(queuedSaleCount()).toBe(0);
  });

  it('keeps sales queued when the server is still unreachable', async () => {
    completeSale.mockRejectedValue(new Error('offline'));
    queueSale(makePayload('key-1'));

    const synced = await syncPendingSales();

    expect(synced).toBe(0);
    expect(queuedSaleCount()).toBe(1);
  });
});

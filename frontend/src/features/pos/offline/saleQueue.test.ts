import { describe, beforeEach, expect, it } from 'vitest';
import type { CompleteSaleRequest } from '../api/pos';
import {
  listQueuedSales,
  queueSale,
  queuedSaleCount,
  removeQueuedSale,
} from './saleQueue';

function makePayload(key: string): CompleteSaleRequest {
  return {
    lines: [{ product_id: 'p1', quantity: 1, unit_price: '1000.00', unit_cost: '500.00' }],
    payments: [{ method: 'cash', amount: '1000.00' }],
    idempotency_key: key,
  };
}

describe('saleQueue', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts empty', () => {
    expect(listQueuedSales()).toEqual([]);
    expect(queuedSaleCount()).toBe(0);
  });

  it('queues a sale with its idempotency key as the id', () => {
    queueSale(makePayload('key-1'));

    const items = listQueuedSales();
    expect(items).toHaveLength(1);
    expect(items[0].id).toBe('key-1');
    expect(items[0].payload.idempotency_key).toBe('key-1');
  });

  it('does not queue the same idempotency key twice', () => {
    queueSale(makePayload('key-1'));
    queueSale(makePayload('key-1'));
    expect(queuedSaleCount()).toBe(1);
  });

  it('removes a queued sale by id', () => {
    queueSale(makePayload('key-1'));
    queueSale(makePayload('key-2'));

    removeQueuedSale('key-1');

    const remaining = listQueuedSales();
    expect(remaining).toHaveLength(1);
    expect(remaining[0].id).toBe('key-2');
  });

  it('recovers from corrupt storage', () => {
    localStorage.setItem('stocktill.pending-sales', 'not-json');
    expect(listQueuedSales()).toEqual([]);
  });
});

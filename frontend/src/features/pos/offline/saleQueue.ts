import type { CompleteSaleRequest } from '../api/pos';

export interface QueuedSale {
  id: string;
  payload: CompleteSaleRequest;
  queuedAt: string;
}

const STORAGE_KEY = 'stocktill.pending-sales';

function read(): QueuedSale[] {
  if (typeof localStorage === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as QueuedSale[]) : [];
  } catch {
    return [];
  }
}

function write(items: QueuedSale[]): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function listQueuedSales(): QueuedSale[] {
  return read();
}

export function queueSale(payload: CompleteSaleRequest): QueuedSale {
  const items = read();
  const entry: QueuedSale = {
    id: payload.idempotency_key,
    payload,
    queuedAt: new Date().toISOString(),
  };
  if (!items.some((item) => item.id === entry.id)) {
    items.push(entry);
    write(items);
  }
  return entry;
}

export function removeQueuedSale(id: string): void {
  write(read().filter((item) => item.id !== id));
}

export function queuedSaleCount(): number {
  return read().length;
}

import { useSyncExternalStore } from 'react';

export type ToastKind = 'success' | 'error' | 'info';

export interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

export interface ToastStore {
  success(message: string, durationMs?: number): number;
  error(message: string, durationMs?: number): number;
  info(message: string, durationMs?: number): number;
  dismiss(id: number): void;
  clear(): void;
  subscribe(listener: () => void): () => void;
  getSnapshot(): ToastItem[];
}

/**
 * A framework-free toast store: any module (including non-React code such as
 * the offline sale sync) can call `toast.success(...)` and the mounted
 * <Toaster /> picks it up.
 */
export function createToastStore(defaultDurationMs = 4500): ToastStore {
  let items: ToastItem[] = [];
  const listeners = new Set<() => void>();
  let nextId = 1;

  const getSnapshot = (): ToastItem[] => items;
  const emit = (): void => {
    listeners.forEach((listener) => listener());
  };

  const dismiss = (id: number): void => {
    const next = items.filter((item) => item.id !== id);
    if (next.length === items.length) return;
    items = next;
    emit();
  };

  const push = (kind: ToastKind, message: string, durationMs = defaultDurationMs): number => {
    const id = nextId++;
    items = [...items, { id, kind, message }];
    emit();
    if (durationMs > 0) {
      setTimeout(() => dismiss(id), durationMs);
    }
    return id;
  };

  return {
    success: (message, durationMs) => push('success', message, durationMs),
    error: (message, durationMs) => push('error', message, durationMs ?? 7000),
    info: (message, durationMs) => push('info', message, durationMs),
    dismiss,
    clear: () => {
      items = [];
      emit();
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getSnapshot,
  };
}

export const toast = createToastStore();

export function useToasts(): ToastItem[] {
  return useSyncExternalStore(toast.subscribe, toast.getSnapshot);
}

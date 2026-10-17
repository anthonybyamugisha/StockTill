import { useEffect } from 'react';
import { BarcodeBuffer } from '../lib/barcodeBuffer';

export interface BarcodeScannerOptions {
  onScan: (barcode: string) => void;
  enabled?: boolean;
}

function isEditableTarget(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  if (!el || typeof el.tagName !== 'string') return false;
  return (
    el.tagName === 'INPUT' ||
    el.tagName === 'TEXTAREA' ||
    el.tagName === 'SELECT' ||
    el.isContentEditable === true
  );
}

/**
 * Listens for keyboard-wedge barcode scanners anywhere on the page so a cashier
 * can scan without focusing a field. Typing inside an input is ignored here and
 * handled by that field instead, which avoids adding the same item twice.
 */
export function useBarcodeScanner({ onScan, enabled = true }: BarcodeScannerOptions): void {
  useEffect(() => {
    if (!enabled) return;

    const buffer = new BarcodeBuffer();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (isEditableTarget(event.target)) {
        buffer.reset();
        return;
      }
      const code = buffer.push(event.key, event.timeStamp);
      if (code !== null) {
        event.preventDefault();
        onScan(code);
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [onScan, enabled]);
}

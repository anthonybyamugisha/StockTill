import { describe, expect, it } from 'vitest';
import { BarcodeBuffer } from './barcodeBuffer';

function feed(buffer: BarcodeBuffer, keys: string, intervalMs: number): string | null {
  let result: string | null = null;
  let at = 0;
  for (const key of keys) {
    result = buffer.push(key, at);
    at += intervalMs;
  }
  return result;
}

describe('BarcodeBuffer', () => {
  it('emits the code for a fast burst terminated by Enter', () => {
    const buffer = new BarcodeBuffer();
    feed(buffer, '5901234123457', 5);
    expect(buffer.push('Enter', 70)).toBe('5901234123457');
  });

  it('ignores human-speed typing', () => {
    const buffer = new BarcodeBuffer();
    feed(buffer, '5901234123457', 200);
    expect(buffer.push('Enter', 2600)).toBeNull();
  });

  it('ignores sequences shorter than the minimum length', () => {
    const buffer = new BarcodeBuffer();
    feed(buffer, '12', 5);
    expect(buffer.push('Enter', 15)).toBeNull();
  });

  it('starts a fresh code after an idle gap', () => {
    const buffer = new BarcodeBuffer();
    buffer.push('9', 0);
    buffer.push('9', 500);
    buffer.push('9', 505);
    expect(buffer.push('Enter', 510)).toBeNull();
  });

  it('ignores modifier and control keys within a scan', () => {
    const buffer = new BarcodeBuffer();
    buffer.push('1', 0);
    buffer.push('Shift', 5);
    buffer.push('2', 10);
    buffer.push('3', 15);
    buffer.push('4', 20);
    expect(buffer.push('Enter', 25)).toBe('1234');
  });
});

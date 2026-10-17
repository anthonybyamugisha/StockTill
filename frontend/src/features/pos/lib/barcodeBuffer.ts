export interface BarcodeBufferOptions {
  minLength?: number;
  maxIntervalMs?: number;
  resetAfterMs?: number;
}

/**
 * Accumulates keystrokes from a keyboard-wedge barcode scanner.
 *
 * A hardware scanner behaves like a very fast keyboard: it types the barcode
 * digits and then presses Enter. This buffer tells that apart from a human
 * typing by requiring a complete, fast burst of characters.
 */
export class BarcodeBuffer {
  private readonly minLength: number;
  private readonly maxIntervalMs: number;
  private readonly resetAfterMs: number;
  private buffer = '';
  private firstAt = 0;
  private lastAt = 0;

  constructor(options: BarcodeBufferOptions = {}) {
    this.minLength = options.minLength ?? 4;
    this.maxIntervalMs = options.maxIntervalMs ?? 50;
    this.resetAfterMs = options.resetAfterMs ?? 100;
  }

  reset(): void {
    this.buffer = '';
    this.firstAt = 0;
    this.lastAt = 0;
  }

  push(key: string, at: number): string | null {
    if (key === 'Enter') {
      const intervals = this.buffer.length - 1;
      const average = intervals > 0 ? (this.lastAt - this.firstAt) / intervals : 0;
      const code = this.buffer.length >= this.minLength ? this.buffer : null;
      this.reset();
      return code !== null && average <= this.maxIntervalMs ? code : null;
    }

    if (key.length !== 1) {
      if (at - this.lastAt > this.resetAfterMs) {
        this.reset();
      }
      return null;
    }

    if (at - this.lastAt > this.resetAfterMs) {
      this.buffer = '';
    }
    if (this.buffer.length === 0) {
      this.firstAt = at;
    }
    this.buffer += key;
    this.lastAt = at;
    return null;
  }
}

export interface DetectedBarcode {
  rawValue: string;
}

export interface BarcodeDetectorInstance {
  detect: (source: CanvasImageSource) => Promise<DetectedBarcode[]>;
}

interface BarcodeDetectorOptions {
  formats?: string[];
}

export interface BarcodeDetectorConstructor {
  new (options?: BarcodeDetectorOptions): BarcodeDetectorInstance;
}

declare global {
  interface Window {
    BarcodeDetector?: BarcodeDetectorConstructor;
  }
}

const SUPPORTED_FORMATS = [
  'ean_13',
  'ean_8',
  'upc_a',
  'upc_e',
  'code_128',
  'code_39',
  'itf',
  'qr_code',
];

export function isCameraScanSupported(): boolean {
  return typeof window !== 'undefined' && typeof window.BarcodeDetector === 'function';
}

export function createBarcodeDetector(): BarcodeDetectorInstance | null {
  const Detector = typeof window !== 'undefined' ? window.BarcodeDetector : undefined;
  if (!Detector) return null;
  return new Detector({ formats: SUPPORTED_FORMATS });
}

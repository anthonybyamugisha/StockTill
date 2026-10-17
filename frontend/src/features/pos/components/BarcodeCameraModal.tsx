import { useEffect, useRef, useState } from 'react';
import { Modal } from '../../../shared/ui/Modal';
import {
  BarcodeDetectorInstance,
  createBarcodeDetector,
  isCameraScanSupported,
} from '../lib/barcodeDetector';

interface BarcodeCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDetected: (barcode: string) => void;
}

export function BarcodeCameraModal({ isOpen, onClose, onDetected }: BarcodeCameraModalProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [supported] = useState(() => isCameraScanSupported());

  useEffect(() => {
    if (!isOpen || !supported) return;

    let stream: MediaStream | null = null;
    let frame = 0;
    let stopped = false;
    const detector: BarcodeDetectorInstance | null = createBarcodeDetector();

    const scanFrame = async (video: HTMLVideoElement) => {
      if (stopped || !detector) return;
      try {
        const codes = await detector.detect(video);
        if (codes.length > 0 && codes[0].rawValue) {
          onDetected(codes[0].rawValue);
          onClose();
          return;
        }
      } catch {
        // Ignore transient frames that fail to decode.
      }
      frame = requestAnimationFrame(() => void scanFrame(video));
    };

    const start = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
        });
        const video = videoRef.current;
        if (!video) return;
        video.srcObject = stream;
        await video.play();
        void scanFrame(video);
      } catch {
        setError('Could not access the camera. Check the browser permission and try again.');
      }
    };

    void start();

    return () => {
      stopped = true;
      cancelAnimationFrame(frame);
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [isOpen, supported, onDetected, onClose]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Scan barcode with camera">
      {supported ? (
        <>
          <div className="overflow-hidden rounded bg-black">
            <video ref={videoRef} className="h-64 w-full object-cover" muted playsInline />
          </div>
          <p className="mt-2 text-sm text-gray-500">Point the camera at the barcode.</p>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </>
      ) : (
        <p className="text-sm text-gray-600">
          This browser does not support camera barcode scanning. Please use a USB or Bluetooth
          scanner, or type the barcode into the search box and press Enter.
        </p>
      )}
    </Modal>
  );
}

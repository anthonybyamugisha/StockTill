import { ReactNode } from 'react';
import { toast, ToastKind, useToasts } from './toast';

const wrapperClasses: Record<ToastKind, string> = {
  success: 'border-green-200',
  error: 'border-red-200',
  info: 'border-primary-200',
};

const iconWrapperClasses: Record<ToastKind, string> = {
  success: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
  info: 'bg-primary-100 text-primary-700',
};

function Icon({ kind }: { kind: ToastKind }) {
  if (kind === 'success') {
    return (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    );
  }
  if (kind === 'error') {
    return (
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
    );
  }
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

export function Toaster(): ReactNode {
  const toasts = useToasts();

  if (toasts.length === 0) return null;

  return (
    <div
      className="pointer-events-none fixed right-4 top-4 z-[100] flex w-full max-w-sm flex-col gap-2"
      aria-live="polite"
    >
      {toasts.map((item) => (
        <div
          key={item.id}
          role={item.kind === 'error' ? 'alert' : 'status'}
          className={`toast-item pointer-events-auto flex items-start gap-3 rounded-lg border bg-white p-3.5 shadow-modal ${wrapperClasses[item.kind]}`}
        >
          <span
            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${iconWrapperClasses[item.kind]}`}
          >
            <Icon kind={item.kind} />
          </span>
          <p className="flex-1 text-sm text-surface-600">{item.message}</p>
          <button
            type="button"
            onClick={() => toast.dismiss(item.id)}
            aria-label="Dismiss notification"
            className="text-surface-400 hover:text-surface-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}

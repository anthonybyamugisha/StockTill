import { Button } from '../../../shared/ui/Button';
import { Spinner } from '../../../shared/ui/Spinner';
import { formatMoney } from '../../../shared/utils/money';
import { PaymentIntent } from '../api/payments';
import {
  intentMessage,
  isFailure,
  isNeedsReview,
  isPending,
  WAITING_MESSAGE,
} from '../lib/intentStatus';
import { mobileNetworkLabel } from '../lib/paymentMethods';

interface PaymentStatusPanelProps {
  intent: PaymentIntent;
  error?: string | null;
  isCancelling: boolean;
  onCancel: () => void;
  onRetry: () => void;
}

function StatusIcon({ tone }: { tone: 'waiting' | 'success' | 'warning' | 'error' }) {
  if (tone === 'waiting') {
    return (
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-50">
        <Spinner size="lg" />
      </div>
    );
  }

  const classes = {
    success: 'bg-green-100 text-green-600',
    warning: 'bg-amber-100 text-amber-600',
    error: 'bg-red-100 text-red-600',
  }[tone];

  const path = {
    success: 'M5 13l4 4L19 7',
    warning: 'M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z',
    error: 'M6 18L18 6M6 6l12 12',
  }[tone];

  return (
    <div className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full ${classes}`}>
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={path} />
      </svg>
    </div>
  );
}

export function PaymentStatusPanel({
  intent,
  error,
  isCancelling,
  onCancel,
  onRetry,
}: PaymentStatusPanelProps) {
  const pending = isPending(intent.status);
  const failure = isFailure(intent.status);
  const review = isNeedsReview(intent.status);

  const tone = pending ? 'waiting' : review ? 'warning' : failure ? 'error' : 'success';
  const title = pending
    ? 'Waiting for approval'
    : review
      ? 'Payment needs review'
      : failure
        ? 'Payment not completed'
        : 'Payment received';

  const message = pending
    ? WAITING_MESSAGE
    : review
      ? intentMessage(intent.status)
      : failure
        ? intentMessage(intent.status, intent.failure_reason)
        : 'Completing the sale...';

  const detailError = error && error !== message ? error : null;

  return (
    <div className="py-2 text-center">
      <StatusIcon tone={tone} />
      <p className="text-lg font-semibold text-surface-600">{title}</p>
      <p className="mt-1 text-sm text-surface-500">{message}</p>

      {detailError && (
        <div className="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-error">{detailError}</div>
      )}

      <div className="mt-4 space-y-1 rounded-lg bg-surface-50 px-4 py-3 text-left text-sm">
        <div className="flex justify-between">
          <span className="text-surface-400">Amount</span>
          <span className="font-semibold">{formatMoney(intent.amount, intent.currency)}</span>
        </div>
        {intent.phone && (
          <div className="flex justify-between">
            <span className="text-surface-400">Phone</span>
            <span>{intent.phone}</span>
          </div>
        )}
        {intent.network && (
          <div className="flex justify-between">
            <span className="text-surface-400">Network</span>
            <span>{mobileNetworkLabel(intent.network)}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-surface-400">Request</span>
          <span className="font-mono text-xs">{intent.tx_ref}</span>
        </div>
      </div>

      {pending && (
        <Button variant="secondary" onClick={onCancel} disabled={isCancelling} className="mt-4">
          {isCancelling ? 'Cancelling...' : 'Cancel request'}
        </Button>
      )}
      {failure && (
        <Button variant="secondary" onClick={onRetry} className="mt-4">
          Try again
        </Button>
      )}
    </div>
  );
}

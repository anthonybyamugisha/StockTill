import type { PaymentIntentStatus } from '../api/payments';

export const WAITING_MESSAGE =
  'Waiting for the customer to approve the payment on their phone...';

export function isPending(status: PaymentIntentStatus): boolean {
  return status === 'pending';
}

export function isSettled(status: PaymentIntentStatus): boolean {
  return status === 'paid' || status === 'needs_review';
}

export function isFailure(status: PaymentIntentStatus): boolean {
  return status === 'failed' || status === 'expired' || status === 'cancelled';
}

export function isNeedsReview(status: PaymentIntentStatus): boolean {
  return status === 'needs_review';
}

export function intentMessage(status: PaymentIntentStatus, reason = ''): string {
  switch (status) {
    case 'pending':
      return WAITING_MESSAGE;
    case 'paid':
      return 'Payment received.';
    case 'needs_review':
      return 'Payment received, but the sale could not be completed. Ask a manager to review it.';
    case 'failed':
      return reason || 'The payment failed. Try again or choose another method.';
    case 'expired':
      return 'The payment request expired. Send a new request.';
    case 'cancelled':
      return 'The payment request was cancelled.';
  }
}

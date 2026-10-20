import { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  cancelPaymentIntent,
  createPaymentIntent,
  CreatePaymentIntentRequest,
  getPaymentIntent,
  PaymentIntent,
} from '../api/payments';
import { intentMessage } from '../lib/intentStatus';
import { getApiErrorMessage } from '../../../shared/http/errors';

const POLL_INTERVAL_MS = 2000;

export function usePaymentIntent() {
  const [intentId, setIntentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const intentQuery = useQuery({
    queryKey: ['payment-intent', intentId],
    queryFn: () => getPaymentIntent(intentId as string),
    enabled: intentId !== null,
    refetchInterval: (query) =>
      query.state.data?.status === 'pending' ? POLL_INTERVAL_MS : false,
  });

  const createMutation = useMutation({
    mutationFn: (payload: CreatePaymentIntentRequest) => createPaymentIntent(payload),
    onSuccess: (intent) => {
      setError(null);
      setIntentId(intent.id);
    },
    onError: (cause) => {
      setError(getApiErrorMessage(cause, 'Could not start the payment.'));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelPaymentIntent(intentId as string),
    onSuccess: () => {
      setIntentId(null);
      setError(null);
    },
    onError: (cause) => {
      setError(getApiErrorMessage(cause, 'Could not cancel the payment.'));
    },
  });

  const intent: PaymentIntent | null = intentQuery.data ?? null;

  useEffect(() => {
    if (!intent) return;
    if (
      intent.status === 'failed' ||
      intent.status === 'expired' ||
      intent.status === 'cancelled' ||
      intent.status === 'needs_review'
    ) {
      setError(intentMessage(intent.status, intent.failure_reason));
    }
  }, [intent]);

  return {
    intent,
    error,
    isStarting: createMutation.isPending,
    isCancelling: cancelMutation.isPending,
    start: (payload: CreatePaymentIntentRequest) => {
      setError(null);
      createMutation.mutate(payload);
    },
    cancel: () => cancelMutation.mutate(),
    reset: () => {
      setIntentId(null);
      setError(null);
      createMutation.reset();
      cancelMutation.reset();
    },
  };
}

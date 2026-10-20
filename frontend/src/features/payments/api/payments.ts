import { apiClient } from '../../../shared/http/client';

export type MobileNetwork = 'mtn' | 'airtel';

export type PaymentIntentStatus =
  | 'pending'
  | 'paid'
  | 'failed'
  | 'expired'
  | 'cancelled'
  | 'needs_review';

export interface PaymentIntent {
  id: string;
  tx_ref: string;
  method: string;
  network: MobileNetwork | null;
  phone: string;
  amount: string;
  currency: string;
  status: PaymentIntentStatus;
  provider: string;
  gateway_reference: string | null;
  checkout_url: string | null;
  failure_reason: string;
  sale_id: string | null;
  created_at: string;
  expires_at: string | null;
}

export interface SalePayloadLine {
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: string;
  unit_cost: string;
  discount_type?: string | null;
  discount_value?: string | null;
}

export interface CreatePaymentIntentRequest {
  method: 'mobile_money';
  amount: string;
  phone: string;
  network: MobileNetwork;
  idempotency_key: string;
  sale: {
    lines: SalePayloadLine[];
    notes?: string;
  };
}

export async function createPaymentIntent(
  data: CreatePaymentIntentRequest,
): Promise<PaymentIntent> {
  const res = await apiClient.post<PaymentIntent>('/payments/intents/', data);
  return res.data;
}

export async function getPaymentIntent(id: string): Promise<PaymentIntent> {
  const res = await apiClient.get<PaymentIntent>(`/payments/intents/${id}/`);
  return res.data;
}

export async function cancelPaymentIntent(id: string, reason = ''): Promise<PaymentIntent> {
  const res = await apiClient.post<PaymentIntent>(`/payments/intents/${id}/cancel/`, {
    reason,
  });
  return res.data;
}

import type { MobileNetwork } from '../api/payments';

export type { MobileNetwork };

export type PaymentMethod = 'cash' | 'mobile_money' | 'card' | 'bank_transfer';

export interface PaymentMethodOption {
  value: PaymentMethod;
  label: string;
  description: string;
}

export const PAYMENT_METHOD_OPTIONS: PaymentMethodOption[] = [
  {
    value: 'cash',
    label: 'Cash',
    description: 'Take cash and give change',
  },
  {
    value: 'mobile_money',
    label: 'Mobile Money',
    description: 'Send a prompt to the customer phone',
  },
];

const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  cash: 'Cash',
  mobile_money: 'Mobile Money',
  card: 'Card',
  bank_transfer: 'Bank Transfer',
};

export const MOBILE_NETWORK_OPTIONS: { value: MobileNetwork; label: string }[] = [
  { value: 'mtn', label: 'MTN MoMo' },
  { value: 'airtel', label: 'Airtel Money' },
];

export function isMobileMoney(method: PaymentMethod): boolean {
  return method === 'mobile_money';
}

export function isManualMethod(method: PaymentMethod): boolean {
  return method === 'card' || method === 'bank_transfer';
}

export function requiresReference(method: PaymentMethod): boolean {
  return isManualMethod(method);
}

export function paymentMethodLabel(method: PaymentMethod | string): string {
  return PAYMENT_METHOD_LABELS[method as PaymentMethod] ?? method;
}

export function mobileNetworkLabel(network: MobileNetwork): string {
  return MOBILE_NETWORK_OPTIONS.find((option) => option.value === network)?.label ?? network;
}

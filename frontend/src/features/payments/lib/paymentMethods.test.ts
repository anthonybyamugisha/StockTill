import { describe, expect, it } from 'vitest';
import {
  isManualMethod,
  isMobileMoney,
  mobileNetworkLabel,
  PAYMENT_METHOD_OPTIONS,
  paymentMethodLabel,
  requiresReference,
} from './paymentMethods';

describe('payment methods', () => {
  it('offers only cash and mobile money in the sale flow', () => {
    expect(PAYMENT_METHOD_OPTIONS.map((option) => option.value)).toEqual([
      'cash',
      'mobile_money',
    ]);
  });

  it('labels every method', () => {
    expect(paymentMethodLabel('cash')).toBe('Cash');
    expect(paymentMethodLabel('mobile_money')).toBe('Mobile Money');
    expect(paymentMethodLabel('card')).toBe('Card');
    expect(paymentMethodLabel('bank_transfer')).toBe('Bank Transfer');
    expect(paymentMethodLabel('cheque')).toBe('cheque');
  });

  it('knows which methods use the gateway', () => {
    expect(isMobileMoney('mobile_money')).toBe(true);
    expect(isMobileMoney('cash')).toBe(false);
    expect(isMobileMoney('card')).toBe(false);
  });

  it('treats card and bank transfer as manual', () => {
    expect(isManualMethod('card')).toBe(true);
    expect(isManualMethod('bank_transfer')).toBe(true);
    expect(isManualMethod('cash')).toBe(false);
    expect(isManualMethod('mobile_money')).toBe(false);
  });

  it('requires a reference only for manual electronic payments', () => {
    expect(requiresReference('card')).toBe(true);
    expect(requiresReference('bank_transfer')).toBe(true);
    expect(requiresReference('cash')).toBe(false);
    expect(requiresReference('mobile_money')).toBe(false);
  });

  it('labels the mobile networks', () => {
    expect(mobileNetworkLabel('mtn')).toBe('MTN MoMo');
    expect(mobileNetworkLabel('airtel')).toBe('Airtel Money');
  });
});

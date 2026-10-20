import { describe, expect, it } from 'vitest';
import {
  calculateChange,
  normalizePhone,
  validatePhone,
  validateReference,
  validateTendered,
} from './validation';

describe('normalizePhone', () => {
  it('turns local numbers into country-code numbers', () => {
    expect(normalizePhone('0772123456')).toBe('256772123456');
    expect(normalizePhone('772123456')).toBe('256772123456');
    expect(normalizePhone('+256 772 123 456')).toBe('256772123456');
    expect(normalizePhone('00256772123456')).toBe('256772123456');
    expect(normalizePhone('(0772) 123-456')).toBe('256772123456');
  });

  it('leaves an empty value alone', () => {
    expect(normalizePhone('')).toBe('');
  });
});

describe('validatePhone', () => {
  it('accepts local and international numbers', () => {
    expect(validatePhone('0772123456')).toBeNull();
    expect(validatePhone('+256772123456')).toBeNull();
  });

  it('rejects numbers that are too short or too long', () => {
    expect(validatePhone('123')).not.toBeNull();
    expect(validatePhone('1234567890123456')).not.toBeNull();
  });
});

describe('validateTendered', () => {
  it('accepts an empty tender as an exact payment', () => {
    expect(validateTendered('', 50000)).toBeNull();
  });

  it('accepts enough cash', () => {
    expect(validateTendered('50000', 50000)).toBeNull();
    expect(validateTendered('60000', 50000)).toBeNull();
  });

  it('rejects short cash and non-numbers', () => {
    expect(validateTendered('40000', 50000)).not.toBeNull();
    expect(validateTendered('banana', 50000)).not.toBeNull();
  });
});

describe('calculateChange', () => {
  it('returns the change for an overpayment', () => {
    expect(calculateChange('60000', 50000)).toBe(10000);
  });

  it('returns zero when the tender is empty or short', () => {
    expect(calculateChange('', 50000)).toBe(0);
    expect(calculateChange('40000', 50000)).toBe(0);
  });

  it('rounds to two decimal places', () => {
    expect(calculateChange('100.006', 100)).toBe(0.01);
  });
});

describe('validateReference', () => {
  it('requires a reference for a card payment', () => {
    expect(validateReference('card', '')).not.toBeNull();
    expect(validateReference('card', 'TXN-123')).toBeNull();
  });

  it('requires a reference for a bank transfer', () => {
    expect(validateReference('bank_transfer', '   ')).not.toBeNull();
  });

  it('does not ask cash or mobile money for a reference', () => {
    expect(validateReference('cash', '')).toBeNull();
    expect(validateReference('mobile_money', '')).toBeNull();
  });
});

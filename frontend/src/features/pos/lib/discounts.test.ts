import { describe, expect, it } from 'vitest';
import { discountAmount, discountPercent, lineGross, lineTotal } from './discounts';

describe('cart discounts', () => {
  it('calculates a percentage discount', () => {
    expect(discountAmount('25000.00', 2, 'percentage', '10')).toBe(5000);
    expect(lineTotal('25000.00', 2, 'percentage', '10')).toBe(45000);
  });

  it('calculates a fixed discount', () => {
    expect(discountAmount('25000.00', 2, 'fixed', '3000')).toBe(3000);
    expect(lineTotal('25000.00', 2, 'fixed', '3000')).toBe(47000);
  });

  it('never discounts more than the line total', () => {
    expect(discountAmount('25000.00', 2, 'fixed', '999999')).toBe(50000);
    expect(lineTotal('25000.00', 2, 'fixed', '999999')).toBe(0);
  });

  it('ignores empty or invalid discounts', () => {
    expect(discountAmount('25000.00', 2, null, null)).toBe(0);
    expect(discountAmount('25000.00', 2, 'percentage', '')).toBe(0);
    expect(discountAmount('25000.00', 2, 'fixed', 'abc')).toBe(0);
  });

  it('reports the discount as a percentage of the cart', () => {
    expect(lineGross('10000.00', 3)).toBe(30000);
    expect(discountPercent(50000, 5000)).toBe(10);
    expect(discountPercent(0, 0)).toBe(0);
  });
});

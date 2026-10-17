import { describe, expect, it } from 'vitest';

import { formatMoney, parseMoney } from './money';

describe('formatMoney', () => {
  it('formats a numeric amount with two decimals and currency prefix', () => {
    expect(formatMoney(25000)).toBe('UGX 25,000.00');
  });

  it('accepts a string amount', () => {
    expect(formatMoney('1500.5')).toBe('UGX 1,500.50');
  });

  it('honours a custom currency', () => {
    expect(formatMoney(10, 'USD')).toBe('USD 10.00');
  });
});

describe('parseMoney', () => {
  it('strips currency symbols, spaces and separators', () => {
    expect(parseMoney('UGX 25,000.00')).toBe(25000);
  });

  it('parses a plain numeric string', () => {
    expect(parseMoney('12.75')).toBe(12.75);
  });
});

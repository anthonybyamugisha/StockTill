import { describe, expect, it } from 'vitest';
import { matchesProductQuery } from './productSearch';

const sugar = { name: 'Sugar 1kg', sku: 'SUG-1', barcode: '111222333' };

describe('matchesProductQuery', () => {
  it('matches everything for a blank query', () => {
    expect(matchesProductQuery(sugar, '')).toBe(true);
    expect(matchesProductQuery(sugar, '   ')).toBe(true);
  });

  it('matches name case-insensitively and partially', () => {
    expect(matchesProductQuery(sugar, 'sugar')).toBe(true);
    expect(matchesProductQuery(sugar, 'UGAR 1')).toBe(true);
  });

  it('matches sku', () => {
    expect(matchesProductQuery(sugar, 'sug-1')).toBe(true);
  });

  it('matches barcode', () => {
    expect(matchesProductQuery(sugar, '22233')).toBe(true);
  });

  it('handles a missing barcode', () => {
    expect(matchesProductQuery({ name: 'Salt', sku: 'SLT' }, 'salt')).toBe(true);
    expect(matchesProductQuery({ name: 'Salt', sku: 'SLT', barcode: null }, '111')).toBe(false);
  });

  it('rejects non-matches', () => {
    expect(matchesProductQuery(sugar, 'rice')).toBe(false);
  });
});

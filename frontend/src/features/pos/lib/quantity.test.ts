import { describe, expect, it } from 'vitest';
import { parseQuantityInput } from './quantity';

describe('parseQuantityInput', () => {
  it('parses plain whole numbers', () => {
    expect(parseQuantityInput('1')).toBe(1);
    expect(parseQuantityInput('24')).toBe(24);
    expect(parseQuantityInput('1000')).toBe(1000);
  });

  it('ignores surrounding whitespace', () => {
    expect(parseQuantityInput(' 12 ')).toBe(12);
  });

  it('accepts leading zeros', () => {
    expect(parseQuantityInput('007')).toBe(7);
  });

  it('rejects zero and negative numbers', () => {
    expect(parseQuantityInput('0')).toBeNull();
    expect(parseQuantityInput('-3')).toBeNull();
  });

  it('rejects empty or partial input', () => {
    expect(parseQuantityInput('')).toBeNull();
    expect(parseQuantityInput('   ')).toBeNull();
  });

  it('rejects decimals, exponents and non-numeric text', () => {
    expect(parseQuantityInput('1.5')).toBeNull();
    expect(parseQuantityInput('1e3')).toBeNull();
    expect(parseQuantityInput('abc')).toBeNull();
    expect(parseQuantityInput('+5')).toBeNull();
  });
});

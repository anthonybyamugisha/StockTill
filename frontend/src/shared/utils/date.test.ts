import { describe, expect, it } from 'vitest';

import { daysAgoISO, formatDate, todayISO } from './date';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

describe('todayISO', () => {
  it('returns a yyyy-mm-dd string', () => {
    expect(todayISO()).toMatch(ISO_DATE);
  });
});

describe('daysAgoISO', () => {
  it('returns today when given zero', () => {
    expect(daysAgoISO(0)).toBe(todayISO());
  });

  it('returns an earlier date for a positive offset', () => {
    expect(daysAgoISO(7) < todayISO()).toBe(true);
  });
});

describe('formatDate', () => {
  it('renders the calendar year of the input', () => {
    expect(formatDate('2026-10-17T09:30:00Z')).toContain('2026');
  });
});

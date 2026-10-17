import { describe, expect, it } from 'vitest';

import {
  daysAgoISO,
  formatDate,
  formatShortDate,
  monthStartISO,
  toISODate,
  todayISO,
} from './date';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

describe('todayISO', () => {
  it('returns a yyyy-mm-dd string', () => {
    expect(todayISO()).toMatch(ISO_DATE);
  });

  it('returns the calendar day of the given moment, not its UTC day', () => {
    expect(todayISO(new Date(2026, 9, 18, 1, 30))).toBe('2026-10-18');
  });
});

describe('daysAgoISO', () => {
  it('returns today when given zero', () => {
    expect(daysAgoISO(0)).toBe(todayISO());
  });

  it('returns an earlier date for a positive offset', () => {
    expect(daysAgoISO(7) < todayISO()).toBe(true);
  });

  it('steps back whole calendar days', () => {
    expect(daysAgoISO(1, new Date(2026, 9, 18, 1, 30))).toBe('2026-10-17');
    expect(daysAgoISO(30, new Date(2026, 9, 18))).toBe('2026-09-18');
  });

  it('crosses a month and a year boundary', () => {
    expect(daysAgoISO(1, new Date(2026, 0, 1))).toBe('2025-12-31');
  });
});

describe('monthStartISO', () => {
  it('returns the first day of the current month', () => {
    expect(monthStartISO(new Date(2026, 9, 18, 1, 30))).toBe('2026-10-01');
  });
});

describe('toISODate', () => {
  it('pads single digit months and days', () => {
    expect(toISODate(new Date(2026, 0, 5))).toBe('2026-01-05');
  });
});

describe('formatShortDate', () => {
  it('shows the day and month of the date itself', () => {
    const label = formatShortDate('2026-10-18');
    expect(label).toContain('18');
    expect(label).toContain('Oct');
  });
});

describe('formatDate', () => {
  it('renders the calendar year of the input', () => {
    expect(formatDate('2026-10-17T09:30:00Z')).toContain('2026');
  });
});

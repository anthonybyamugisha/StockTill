import { describe, expect, it } from 'vitest';
import {
  intentMessage,
  isFailure,
  isNeedsReview,
  isPending,
  isSettled,
  WAITING_MESSAGE,
} from './intentStatus';

describe('intent status', () => {
  it('knows a pending payment', () => {
    expect(isPending('pending')).toBe(true);
    expect(isPending('paid')).toBe(false);
    expect(isSettled('pending')).toBe(false);
  });

  it('knows the settled states', () => {
    expect(isSettled('paid')).toBe(true);
    expect(isSettled('needs_review')).toBe(true);
    expect(isSettled('failed')).toBe(false);
  });

  it('knows the failure states', () => {
    expect(isFailure('failed')).toBe(true);
    expect(isFailure('expired')).toBe(true);
    expect(isFailure('cancelled')).toBe(true);
    expect(isFailure('paid')).toBe(false);
  });

  it('flags a payment that needs review', () => {
    expect(isNeedsReview('needs_review')).toBe(true);
    expect(isNeedsReview('paid')).toBe(false);
  });

  it('explains the waiting state', () => {
    expect(intentMessage('pending')).toBe(WAITING_MESSAGE);
  });

  it('uses the gateway reason for a failure', () => {
    expect(intentMessage('failed', 'Insufficient funds')).toBe('Insufficient funds');
    expect(intentMessage('failed')).toContain('Try again');
  });

  it('tells the cashier to ask a manager when the sale could not complete', () => {
    expect(intentMessage('needs_review')).toContain('manager');
  });

  it('explains expiry and cancellation', () => {
    expect(intentMessage('expired')).toContain('expired');
    expect(intentMessage('cancelled')).toContain('cancelled');
  });
});

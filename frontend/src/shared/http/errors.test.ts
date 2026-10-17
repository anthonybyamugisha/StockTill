import { describe, expect, it } from 'vitest';
import { getApiErrorMessage } from './errors';

function axiosError(data: unknown, status = 400): unknown {
  return { isAxiosError: true, response: { status, data } };
}

describe('getApiErrorMessage', () => {
  it('prefers the API detail message', () => {
    expect(getApiErrorMessage(axiosError({ detail: 'Insufficient stock for Sugar.' }))).toBe(
      'Insufficient stock for Sugar.',
    );
  });

  it('falls back to the first field error', () => {
    expect(getApiErrorMessage(axiosError({ payments: ['This field is required.'] }))).toBe(
      'This field is required.',
    );
  });

  it('returns a status message when the body has no message', () => {
    expect(getApiErrorMessage(axiosError({}))).toBe('Request failed (status 400).');
  });

  it('uses the message of a plain Error', () => {
    expect(getApiErrorMessage(new Error('boom'))).toBe('boom');
  });

  it('returns the fallback for unknown values', () => {
    expect(getApiErrorMessage(null, 'fallback')).toBe('fallback');
  });
});

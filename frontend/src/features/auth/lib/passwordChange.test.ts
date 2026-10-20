import { describe, expect, it } from 'vitest';
import { isPasswordChangeRequired, shouldOpenPasswordChange } from './passwordChange';

describe('password change response handling', () => {
  it('recognises the pending password code', () => {
    expect(isPasswordChangeRequired({ code: 'password_change_required' })).toBe(true);
  });

  it('ignores other error payloads', () => {
    expect(isPasswordChangeRequired({ code: 'permission_denied' })).toBe(false);
    expect(isPasswordChangeRequired(null)).toBe(false);
    expect(isPasswordChangeRequired('password_change_required')).toBe(false);
  });

  it('opens the change password page once', () => {
    expect(shouldOpenPasswordChange('/', { code: 'password_change_required' })).toBe(true);
    expect(shouldOpenPasswordChange('/change-password', { code: 'password_change_required' })).toBe(
      false,
    );
    expect(shouldOpenPasswordChange('/', { code: 'permission_denied' })).toBe(false);
  });
});

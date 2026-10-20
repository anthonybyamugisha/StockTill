import { describe, expect, it } from 'vitest';

import { homePathFor } from './redirect';

describe('homePathFor', () => {
  it('sends a pending user to the password change screen', () => {
    expect(homePathFor({ must_change_password: true })).toBe('/change-password');
  });

  it('sends a settled user to the dashboard', () => {
    expect(homePathFor({ must_change_password: false })).toBe('/');
  });
});

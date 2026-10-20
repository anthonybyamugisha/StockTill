import { describe, expect, it } from 'vitest';

import { passwordIssue } from './passwordPolicy';

describe('passwordIssue', () => {
  it('rejects a password shorter than eight characters', () => {
    expect(passwordIssue('short1')).toBe('Use at least 8 characters');
  });

  it('accepts a password with letters and numbers', () => {
    expect(passwordIssue('permanent12')).toBeNull();
  });
});

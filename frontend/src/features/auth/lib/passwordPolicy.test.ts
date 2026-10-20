import { describe, expect, it } from 'vitest';

import { confirmationIssue, passwordIssue } from './passwordPolicy';

describe('passwordIssue', () => {
  it('rejects a password shorter than eight characters', () => {
    expect(passwordIssue('short1')).toBe('Use at least 8 characters');
  });

  it('accepts a password with letters and numbers', () => {
    expect(passwordIssue('permanent12')).toBeNull();
  });

  it('rejects letters without a number', () => {
    expect(passwordIssue('onlyletters')).toBe('Include at least one letter and one number');
  });

  it('rejects numbers without a letter', () => {
    expect(passwordIssue('12345678')).toBe('Include at least one letter and one number');
  });
});

describe('confirmationIssue', () => {
  it('rejects a mismatched confirmation', () => {
    expect(confirmationIssue('permanent12', 'permanent13')).toBe('Passwords do not match');
  });

  it('accepts a matching confirmation', () => {
    expect(confirmationIssue('permanent12', 'permanent12')).toBeNull();
  });
});
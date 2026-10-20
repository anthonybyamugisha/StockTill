export const MIN_PASSWORD_LENGTH = 8;

export function passwordIssue(password: string): string | null {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Use at least ${MIN_PASSWORD_LENGTH} characters`;
  }
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    return 'Include at least one letter and one number';
  }
  return null;
}

export function confirmationIssue(password: string, confirmation: string): string | null {
  if (confirmation !== password) {
    return 'Passwords do not match';
  }
  return null;
}

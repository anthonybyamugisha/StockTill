const PASSWORD_CHANGE_CODE = 'password_change_required';

export function isPasswordChangeRequired(data: unknown): boolean {
  return (
    typeof data === 'object' &&
    data !== null &&
    'code' in data &&
    (data as { code?: unknown }).code === PASSWORD_CHANGE_CODE
  );
}

export function shouldOpenPasswordChange(pathname: string, data: unknown): boolean {
  return isPasswordChangeRequired(data) && pathname !== '/change-password';
}

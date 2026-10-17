export function isOffline(): boolean {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}

export function isNetworkError(error: unknown): boolean {
  if (isOffline()) return true;
  if (!error || typeof error !== 'object') return false;
  const candidate = error as { response?: unknown; request?: unknown; code?: string };
  if (candidate.response !== undefined) return false;
  return candidate.request !== undefined || candidate.code === 'ERR_NETWORK';
}

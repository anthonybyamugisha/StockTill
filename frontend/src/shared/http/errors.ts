import axios from 'axios';

/**
 * Turns an unknown error into the most useful message available. The API returns
 * `{"detail": "..."}` for domain failures, but Axios only exposes a generic
 * message, so we read the response body first.
 */
export function getApiErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as unknown;
    if (typeof data === 'string' && data.trim()) return data;
    if (data && typeof data === 'object') {
      const detail = (data as { detail?: unknown }).detail;
      if (typeof detail === 'string' && detail) return detail;
      for (const value of Object.values(data as Record<string, unknown>)) {
        if (typeof value === 'string' && value) return value;
        if (Array.isArray(value) && typeof value[0] === 'string') return value[0];
      }
    }
    if (error.response) return `Request failed (status ${error.response.status}).`;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

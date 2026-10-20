import axios, { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { shouldOpenPasswordChange } from '../../features/auth/lib/passwordChange';

const baseURL = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1];
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const url = error.config?.url ?? '';
      const isAuthCheck = url.includes('/accounts/me/');
      if (!isAuthCheck && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 403 &&
      shouldOpenPasswordChange(window.location.pathname, error.response.data)
    ) {
      window.location.href = '/change-password';
    }
    return Promise.reject(error);
  },
);

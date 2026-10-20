import { apiClient } from '../../../shared/http/client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'manager' | 'cashier';
  is_active: boolean;
  must_change_password: boolean;
}

export async function login(data: LoginRequest): Promise<User> {
  const res = await apiClient.post<User>('/accounts/login/', data);
  return res.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/accounts/logout/');
}

export async function getCurrentUser(): Promise<User> {
  const res = await apiClient.get<User>('/accounts/me/');
  const data = res.data;
  if (data && typeof data === 'object' && 'email' in data) {
    return data;
  }
  throw new Error('Not authenticated');
}

export async function changePassword(data: ChangePasswordRequest): Promise<User> {
  const res = await apiClient.post<User>('/accounts/change-password/', data);
  return res.data;
}

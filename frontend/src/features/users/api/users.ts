import { apiClient } from '../../../shared/http/client';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'manager' | 'cashier';
  is_active: boolean;
  must_change_password: boolean;
  last_login: string | null;
}

export interface Cashier {
  id: string;
  first_name: string;
  last_name: string;
}

export async function listCashiers(): Promise<Cashier[]> {
  const res = await apiClient.get<Cashier[]>('/accounts/cashiers/');
  return res.data;
}

export async function listUsers(): Promise<User[]> {
  const res = await apiClient.get<User[]>('/accounts/users/');
  return res.data;
}

export async function createUser(data: {
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  password: string;
}): Promise<User> {
  const res = await apiClient.post<User>('/accounts/users/', data);
  return res.data;
}

export async function updateUser(
  id: string,
  data: Partial<Pick<User, 'first_name' | 'last_name' | 'role'>>,
): Promise<User> {
  const res = await apiClient.patch<User>(`/accounts/users/${id}/`, data);
  return res.data;
}

export async function deactivateUser(id: string): Promise<void> {
  await apiClient.delete(`/accounts/users/${id}/`);
}

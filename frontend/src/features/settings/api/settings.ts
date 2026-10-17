import { apiClient } from '../../../shared/http/client';

export interface BusinessSettings {
  business_name: string;
  address: string;
  phone: string;
  email: string;
  currency: string;
  receipt_header: string;
  receipt_footer: string;
  cashier_discount_limit: string;
  tax_rate: string;
  logo_url: string | null;
}

export async function getSettings(): Promise<BusinessSettings> {
  const res = await apiClient.get<BusinessSettings>('/settings/');
  return res.data;
}

export async function updateSettings(data: BusinessSettings): Promise<BusinessSettings> {
  const res = await apiClient.put<BusinessSettings>('/settings/', data);
  return res.data;
}

import { apiClient } from '../../../shared/http/client';

export interface Sale {
  id: string;
  receipt_number: string;
  cashier_id: string;
  status: string;
  lines: Array<{
    id: string;
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: string;
    unit_cost: string;
  }>;
  payments: Array<{
    id: string;
    method: string;
    amount: string;
  }>;
  subtotal: string;
  total_discount: string;
  total: string;
  created_at: string;
}

export async function listSales(params?: {
  cashier_id?: string;
  status?: string;
  payment_method?: string;
  date_from?: string;
  date_to?: string;
  receipt_number?: string;
}): Promise<Sale[]> {
  const res = await apiClient.get<Sale[]>('/sales/', { params });
  return res.data;
}

export async function getSale(saleId: string): Promise<Sale> {
  const res = await apiClient.get<Sale>(`/sales/${saleId}/`);
  return res.data;
}

export async function refundSale(data: {
  sale_id: string;
  line_id?: string;
  quantity: number;
  reason: string;
  restock: boolean;
}): Promise<{ id: string; status: string }> {
  const res = await apiClient.post('/sales/refund/', data);
  return res.data;
}

export async function voidSale(data: {
  sale_id: string;
  reason: string;
}): Promise<Sale> {
  const res = await apiClient.post<Sale>('/sales/void/', data);
  return res.data;
}

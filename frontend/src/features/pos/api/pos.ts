import { apiClient } from '../../../shared/http/client';

export interface CartItem {
  product_id: string;
  name: string;
  quantity: number;
  unit_price: string;
  unit_cost: string;
}

export interface PaymentInput {
  method: 'cash' | 'mobile_money' | 'card' | 'bank_transfer';
  amount: string;
  tendered?: string;
  reference?: string;
  provider?: string;
}

export interface CompleteSaleRequest {
  lines: Array<{
    product_id: string;
    quantity: number;
    unit_price: string;
    unit_cost: string;
  }>;
  payments: PaymentInput[];
  idempotency_key: string;
}

export interface Sale {
  id: string;
  receipt_number: string;
  status: string;
  lines: Array<{
    id: string;
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: string;
  }>;
  payments: Array<{
    method: string;
    amount: string;
  }>;
  subtotal: string;
  total_discount: string;
  total: string;
  created_at: string;
}

export async function completeSale(data: CompleteSaleRequest): Promise<Sale> {
  const res = await apiClient.post<Sale>('/sales/', data);
  return res.data;
}

export async function searchProducts(query: string) {
  const res = await apiClient.get('/catalog/products/', { params: { q: query } });
  return res.data;
}

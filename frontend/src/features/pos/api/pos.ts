import { apiClient } from '../../../shared/http/client';

export interface CartItem {
  product_id: string;
  name: string;
  quantity: number;
  unit_price: string;
  unit_cost: string;
}

export interface ProductLookup {
  id: string;
  name: string;
  sku: string;
  barcode: string | null;
  selling_price: string;
  buying_cost: string;
  category_id: string | null;
  minimum_stock_level: number;
  image_url: string | null;
}

export interface CategoryLookup {
  id: string;
  name: string;
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

export async function listAvailableProducts(categoryId?: string): Promise<ProductLookup[]> {
  const res = await apiClient.get<ProductLookup[]>('/catalog/products/', {
    params: { active_only: true, category_id: categoryId },
  });
  return res.data;
}

export async function listCategories(): Promise<CategoryLookup[]> {
  const res = await apiClient.get<CategoryLookup[]>('/catalog/categories/');
  return res.data;
}

export async function lookupProductByBarcode(barcode: string): Promise<ProductLookup> {
  const res = await apiClient.get<ProductLookup>('/catalog/products/by-barcode/', {
    params: { barcode },
  });
  return res.data;
}

import { apiClient } from '../../../shared/http/client';

export interface StockItem {
  product_id: string;
  product_name: string;
  sku: string | null;
  quantity_on_hand: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface StockMovement {
  id: string;
  product_id: string;
  quantity: number;
  movement_type: string;
  reason: string;
  reference: string | null;
  unit_cost: string;
  user_id: string | null;
  timestamp: string;
}

export interface StockValuationRow {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_cost: string;
  value: string;
}

export interface StockValuation {
  total: string;
  by_product: StockValuationRow[];
}

export interface AdjustStockRequest {
  product_id: string;
  quantity: number;
  movement_type: string;
  reason: string;
  reference?: string;
  unit_cost?: string;
}

export async function adjustStock(data: AdjustStockRequest): Promise<StockMovement> {
  const res = await apiClient.post<StockMovement>('/inventory/adjust/', data);
  return res.data;
}

export async function getStockItem(productId: string): Promise<StockItem> {
  const res = await apiClient.get<StockItem>(`/inventory/items/${productId}/`);
  return res.data;
}

export async function listStockItems(): Promise<StockItem[]> {
  const res = await apiClient.get<StockItem[]>('/inventory/items/');
  return res.data;
}

export async function getStockHistory(productId: string): Promise<StockMovement[]> {
  const res = await apiClient.get<StockMovement[]>(`/inventory/history/${productId}/`);
  return res.data;
}

export async function getValuation(): Promise<StockValuation> {
  const res = await apiClient.get<StockValuation>('/inventory/valuation/');
  return res.data;
}

export async function getLowStock(): Promise<StockItem[]> {
  const res = await apiClient.get<StockItem[]>('/inventory/low-stock/');
  return res.data;
}

export async function getOutOfStock(): Promise<StockItem[]> {
  const res = await apiClient.get<StockItem[]>('/inventory/out-of-stock/');
  return res.data;
}

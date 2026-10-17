import { apiClient } from '../../../shared/http/client';

export interface DashboardStats {
  today_sales: number;
  week_sales: number;
  month_sales: number;
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  average_sale_value: string;
  gross_profit: string;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await apiClient.get<DashboardStats>('/reporting/dashboard/');
  return res.data;
}

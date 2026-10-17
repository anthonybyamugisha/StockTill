import { apiClient } from '../../../shared/http/client';

export interface DashboardStats {
  today_sales: number;
  today_revenue: string;
  week_sales: number;
  week_revenue: string;
  month_sales: number;
  month_revenue: string;
  total_transactions: number;
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

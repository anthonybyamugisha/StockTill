import { apiClient } from '../../../shared/http/client';

export interface SalesSummary {
  total_sales: number;
  total_revenue: string;
  total_cost: string;
  gross_profit: string;
  average_sale_value: string;
  date_from: string;
  date_to: string;
}

export interface TopProduct {
  product_id: string;
  product_name: string;
  quantity_sold: number;
  revenue: string;
}

export interface DailySales {
  date: string;
  transaction_count: number;
  total: string;
}

export interface CashierSales {
  cashier_id: string;
  cashier_name: string;
  transaction_count: number;
  total: string;
}

export interface ProfitReport {
  date: string;
  total_revenue: string;
  total_cost: string;
  gross_profit: string;
}

export interface LowStockItem {
  product_id: string;
  product_name: string;
  sku: string;
  quantity_on_hand: number;
  minimum_level: number;
}

export async function getSalesSummary(dateFrom: string, dateTo: string): Promise<SalesSummary> {
  const res = await apiClient.get<SalesSummary>('/reporting/sales-summary/', {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return res.data;
}

export async function getTopProducts(dateFrom: string, dateTo: string): Promise<TopProduct[]> {
  const res = await apiClient.get<TopProduct[]>('/reporting/top-products/', {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return res.data;
}

export async function getDailySales(dateFrom: string, dateTo: string): Promise<DailySales[]> {
  const res = await apiClient.get<DailySales[]>('/reporting/daily-sales/', {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return res.data;
}

export async function getCashierSales(dateFrom: string, dateTo: string): Promise<CashierSales[]> {
  const res = await apiClient.get<CashierSales[]>('/reporting/cashier-sales/', {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return res.data;
}

export async function getProfitReport(dateFrom: string, dateTo: string): Promise<ProfitReport[]> {
  const res = await apiClient.get<ProfitReport[]>('/reporting/profit/', {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return res.data;
}

export async function getLowStockItems(): Promise<LowStockItem[]> {
  const res = await apiClient.get<LowStockItem[]>('/reporting/low-stock/');
  return res.data;
}

export async function downloadSalesReportCsv(dateFrom: string, dateTo: string): Promise<void> {
  const res = await apiClient.get<Blob>('/reporting/sales-report/csv/', {
    params: { date_from: dateFrom, date_to: dateTo },
    responseType: 'blob',
  });

  const url = URL.createObjectURL(res.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'sales_report.csv';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

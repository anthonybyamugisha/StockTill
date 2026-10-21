import { apiClient } from '../../../shared/http/client';
import { reportExport } from '../lib/export';

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

export interface PaymentMethodSales {
  method: string;
  count: number;
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

export interface InventoryReport {
  total_products: number;
  total_value: string;
  low_stock_count: number;
  out_of_stock_count: number;
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

export async function getSalesByPaymentMethod(
  dateFrom: string,
  dateTo: string,
): Promise<PaymentMethodSales[]> {
  const res = await apiClient.get<PaymentMethodSales[]>('/reporting/by-payment-method/', {
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

export async function getInventoryReport(): Promise<InventoryReport> {
  const res = await apiClient.get<InventoryReport>('/reporting/inventory/');
  return res.data;
}

async function downloadCsv(
  path: string,
  filename: string,
  params?: Record<string, string>,
): Promise<void> {
  const res = await apiClient.get<Blob>(path, { params, responseType: 'blob' });

  const url = URL.createObjectURL(res.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function downloadReportCsv(
  reportId: string,
  dateFrom: string,
  dateTo: string,
): Promise<void> {
  const config = reportExport(reportId);
  if (!config) {
    throw new Error(`Unknown report: ${reportId}`);
  }

  const params = config.dated ? { date_from: dateFrom, date_to: dateTo } : undefined;
  await downloadCsv(config.path, config.filename, params);
}

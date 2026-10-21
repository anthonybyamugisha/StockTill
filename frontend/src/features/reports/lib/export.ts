export interface ReportExport {
  path: string;
  filename: string;
  dated: boolean;
}

const EXPORTS: Record<string, ReportExport> = {
  sales: {
    path: '/reporting/sales-report/csv/',
    filename: 'sales_report.csv',
    dated: true,
  },
  profit: {
    path: '/reporting/profit/csv/',
    filename: 'profit_report.csv',
    dated: true,
  },
  inventory: {
    path: '/reporting/inventory/csv/',
    filename: 'inventory_report.csv',
    dated: false,
  },
  products: {
    path: '/reporting/top-products/csv/',
    filename: 'top_products.csv',
    dated: true,
  },
  lowstock: {
    path: '/reporting/low-stock/csv/',
    filename: 'low_stock.csv',
    dated: false,
  },
  cashier: {
    path: '/reporting/cashier-sales/csv/',
    filename: 'cashier_sales.csv',
    dated: true,
  },
  payments: {
    path: '/reporting/by-payment-method/csv/',
    filename: 'sales_by_payment_method.csv',
    dated: true,
  },
};

export function reportExport(reportId: string): ReportExport | undefined {
  return EXPORTS[reportId];
}

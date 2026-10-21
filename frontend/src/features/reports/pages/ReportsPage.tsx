import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getSalesSummary, getTopProducts, getDailySales, getCashierSales, getProfitReport, getLowStockItems, getInventoryReport, getSalesByPaymentMethod, downloadReportCsv, CashierSales, PaymentMethodSales } from '../api/reports';
import { paymentMethodLabel } from '../../payments/lib/paymentMethods';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';
import { formatShortDate, daysAgoISO, todayISO } from '../../../shared/utils/date';
import { formatMoney } from '../../../shared/utils/money';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { reportExport } from '../lib/export';

export function ReportsPage() {
  const [activeReport, setActiveReport] = useState('sales');
  const [dateFrom, setDateFrom] = useState(daysAgoISO(30));
  const [dateTo, setDateTo] = useState(todayISO());

  const reports = [
    { id: 'sales', label: 'Sales Report' },
    { id: 'profit', label: 'Profit Report' },
    { id: 'inventory', label: 'Inventory Report' },
    { id: 'products', label: 'Best Sellers' },
    { id: 'lowstock', label: 'Low Stock' },
    { id: 'cashier', label: 'Sales by Cashier' },
    { id: 'payments', label: 'Payment Methods' },
  ];

  const activeLabel = reports.find((r) => r.id === activeReport)?.label ?? 'Report';
  const activeExport = reportExport(activeReport);

  const exportMutation = useMutation({
    mutationFn: () => downloadReportCsv(activeReport, dateFrom, dateTo),
    onSuccess: () => toast.success(`${activeLabel} exported as CSV`),
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not export the report')),
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {reports.map((r) => (
          <button
            key={r.id}
            onClick={() => setActiveReport(r.id)}
            className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
              activeReport === r.id
                ? 'bg-primary-500 text-white'
                : 'bg-white text-surface-600 border border-surface-200 hover:bg-surface-50'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      <Card>
        <div className="flex items-end gap-4">
          {activeExport?.dated && (
            <>
              <Input label="From" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
              <Input label="To" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </>
          )}
          <Button
            variant="secondary"
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending}
          >
            {exportMutation.isPending ? 'Exporting...' : 'Export CSV'}
          </Button>
        </div>
      </Card>

      {activeReport === 'sales' && <SalesReport dateFrom={dateFrom} dateTo={dateTo} />}
      {activeReport === 'profit' && <ProfitReport dateFrom={dateFrom} dateTo={dateTo} />}
      {activeReport === 'inventory' && <InventoryReport />}
      {activeReport === 'products' && <BestSellers dateFrom={dateFrom} dateTo={dateTo} />}
      {activeReport === 'lowstock' && <LowStockReport />}
      {activeReport === 'cashier' && <CashierReport dateFrom={dateFrom} dateTo={dateTo} />}
      {activeReport === 'payments' && <PaymentMethodsReport dateFrom={dateFrom} dateTo={dateTo} />}
    </div>
  );
}

function SalesReport({ dateFrom, dateTo }: { dateFrom: string; dateTo: string }) {
  const { data: summary } = useQuery({
    queryKey: ['salesSummary', dateFrom, dateTo],
    queryFn: () => getSalesSummary(dateFrom, dateTo),
  });

  const { data: dailySales } = useQuery({
    queryKey: ['dailySales', dateFrom, dateTo],
    queryFn: () => getDailySales(dateFrom, dateTo),
  });

  const trend = useMemo(
    () =>
      (dailySales ?? []).map((day) => ({
        label: formatShortDate(day.date),
        date: day.date,
        sales: Number(day.total),
        transactions: day.transaction_count,
      })),
    [dailySales],
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-surface-400">Total Sales</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">{summary?.total_sales ?? 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Revenue</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">UGX {summary?.total_revenue ?? 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Cost</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">UGX {summary?.total_cost ?? 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Gross Profit</p>
          <p className="mt-1 text-2xl font-semibold text-success">{summary?.gross_profit ?? 0}</p>
        </div>
      </div>
      <Card title="Daily Sales Trend" subtitle={`${formatShortDate(dateFrom)} to ${formatShortDate(dateTo)}`}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} minTickGap={24} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              labelFormatter={(_, payload) => payload?.[0]?.payload?.date ?? ''}
              formatter={(value: number) => [formatMoney(value), 'Sales']}
            />
            <Line type="monotone" dataKey="sales" stroke="#0078d4" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

function ProfitReport({ dateFrom, dateTo }: { dateFrom: string; dateTo: string }) {
  const { data: profit } = useQuery({
    queryKey: ['profit', dateFrom, dateTo],
    queryFn: () => getProfitReport(dateFrom, dateTo),
  });

  const days = useMemo(
    () =>
      (profit ?? []).map((day) => ({
        label: formatShortDate(day.date),
        revenue: Number(day.total_revenue),
        profit: Number(day.gross_profit),
      })),
    [profit],
  );

  return (
    <Card title="Daily Profit" subtitle={`${formatShortDate(dateFrom)} to ${formatShortDate(dateTo)}`}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={days}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} minTickGap={24} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: number) => formatMoney(value)} />
          <Legend />
          <Bar dataKey="revenue" fill="#0078d4" name="Revenue" />
          <Bar dataKey="profit" fill="#107c10" name="Profit" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

function InventoryReport() {
  const { data: inventory } = useQuery({
    queryKey: ['inventoryReport'],
    queryFn: getInventoryReport,
  });

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="card">
        <p className="text-sm text-surface-400">Total Products</p>
        <p className="mt-1 text-2xl font-semibold text-surface-600">
          {inventory?.total_products ?? 0}
        </p>
      </div>
      <div className="card">
        <p className="text-sm text-surface-400">Inventory Value</p>
        <p className="mt-1 text-2xl font-semibold text-surface-600">
          UGX {inventory?.total_value ?? '0.00'}
        </p>
      </div>
      <div className="card">
        <p className="text-sm text-surface-400">Low Stock</p>
        <p className="mt-1 text-2xl font-semibold text-warning">
          {inventory?.low_stock_count ?? 0}
        </p>
      </div>
      <div className="card">
        <p className="text-sm text-surface-400">Out of Stock</p>
        <p className="mt-1 text-2xl font-semibold text-error">
          {inventory?.out_of_stock_count ?? 0}
        </p>
      </div>
    </div>
  );
}

function BestSellers({ dateFrom, dateTo }: { dateFrom: string; dateTo: string }) {
  const { data: products } = useQuery({
    queryKey: ['topProducts', dateFrom, dateTo],
    queryFn: () => getTopProducts(dateFrom, dateTo),
  });

  return (
    <Card title="Best Selling Products">
      <Table
        columns={[
          { key: 'product', header: 'Product', render: (p: any) => p.product_name },
          { key: 'quantity', header: 'Qty Sold', render: (p: any) => p.quantity_sold },
          { key: 'revenue', header: 'Revenue', render: (p: any) => `UGX ${p.revenue}` },
        ]}
        data={products || []}
        keyExtractor={(p) => p.product_id}
        emptyMessage="No sales data"
      />
    </Card>
  );
}

function LowStockReport() {
  const { data: items } = useQuery({
    queryKey: ['lowStock'],
    queryFn: () => getLowStockItems(),
  });

  return (
    <Card title="Low Stock Alert">
      <Table
        columns={[
          { key: 'product', header: 'Product', render: (i: any) => (
            <div>
              <p className="font-medium">{i.product_name}</p>
              <p className="text-xs text-surface-400">{i.sku}</p>
            </div>
          )},
          { key: 'quantity', header: 'In Stock', render: (i: any) => <Badge variant="warning">{i.quantity_on_hand}</Badge> },
          { key: 'minimum', header: 'Min Level', render: (i: any) => i.minimum_level },
        ]}
        data={items || []}
        keyExtractor={(i) => i.product_id}
        emptyMessage="No low stock items"
      />
    </Card>
  );
}

function CashierReport({ dateFrom, dateTo }: { dateFrom: string; dateTo: string }) {
  const { data: cashiers } = useQuery({
    queryKey: ['cashierSales', dateFrom, dateTo],
    queryFn: () => getCashierSales(dateFrom, dateTo),
  });

  return (
    <Card title="Sales by Cashier">
      <Table
        columns={[
          { key: 'cashier', header: 'Cashier', render: (c: CashierSales) => c.cashier_name || c.cashier_id.slice(0, 8) },
          { key: 'count', header: 'Transactions', render: (c: CashierSales) => c.transaction_count },
          { key: 'total', header: 'Total', render: (c: CashierSales) => `UGX ${c.total}` },
        ]}
        data={cashiers || []}
        keyExtractor={(c) => c.cashier_id}
        emptyMessage="No cashier data"
      />
    </Card>
  );
}


function PaymentMethodsReport({ dateFrom, dateTo }: { dateFrom: string; dateTo: string }) {
  const { data: paymentMethods } = useQuery({
    queryKey: ['paymentMethods', dateFrom, dateTo],
    queryFn: () => getSalesByPaymentMethod(dateFrom, dateTo),
  });

  const rows = useMemo(
    () =>
      (paymentMethods ?? []).map((entry) => ({
        method: entry.method,
        label: paymentMethodLabel(entry.method),
        count: entry.count,
        total: Number(entry.total),
      })),
    [paymentMethods],
  );

  const total = rows.reduce((sum, row) => sum + row.total, 0);
  const totalSales = rows.reduce((sum, row) => sum + row.count, 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <p className="text-sm text-surface-400">Paid Sales</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">{totalSales}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Collected</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">{formatMoney(total)}</p>
        </div>
      </div>

      <Card title="Payment Methods" subtitle={`${formatShortDate(dateFrom)} to ${formatShortDate(dateTo)}`}>
        <ResponsiveContainer width="100%" height={Math.max(180, rows.length * 60)}>
          <BarChart data={rows} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="label" tick={{ fontSize: 12 }} width={140} />
            <Tooltip formatter={(value: number) => formatMoney(value)} />
            <Bar dataKey="total" fill="#0078d4" name="Sales" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card>
        <Table
          columns={[
            {
              key: 'method',
              header: 'Method',
              render: (row: PaymentMethodSales) => paymentMethodLabel(row.method),
            },
            {
              key: 'count',
              header: 'Transactions',
              render: (row: PaymentMethodSales) => row.count,
            },
            {
              key: 'total',
              header: 'Total',
              render: (row: PaymentMethodSales) => formatMoney(row.total),
            },
            {
              key: 'share',
              header: 'Share',
              render: (row: PaymentMethodSales) =>
                total > 0 ? `${((Number(row.total) / total) * 100).toFixed(1)}%` : '0.0%',
            },
          ]}
          data={paymentMethods || []}
          keyExtractor={(row) => row.method}
          emptyMessage="No payment data for this period"
        />
      </Card>
    </div>
  );
}

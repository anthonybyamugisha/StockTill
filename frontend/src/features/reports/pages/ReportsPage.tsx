import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getSalesSummary, getTopProducts, getDailySales, getCashierSales, getProfitReport, getLowStockItems, downloadSalesReportCsv, CashierSales } from '../api/reports';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';
import { formatShortDate, daysAgoISO, todayISO } from '../../../shared/utils/date';
import { formatMoney } from '../../../shared/utils/money';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';

export function ReportsPage() {
  const [activeReport, setActiveReport] = useState('sales');
  const [dateFrom, setDateFrom] = useState(daysAgoISO(30));
  const [dateTo, setDateTo] = useState(todayISO());

  const exportMutation = useMutation({
    mutationFn: () => downloadSalesReportCsv(dateFrom, dateTo),
    onSuccess: () => toast.success('Sales report exported as CSV'),
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not export the report')),
  });

  const reports = [
    { id: 'sales', label: 'Sales Report' },
    { id: 'profit', label: 'Profit Report' },
    { id: 'inventory', label: 'Inventory Report' },
    { id: 'products', label: 'Best Sellers' },
    { id: 'lowstock', label: 'Low Stock' },
    { id: 'cashier', label: 'Sales by Cashier' },
  ];

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
          <Input label="From" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <Input label="To" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
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
  const { data: summary } = useQuery({
    queryKey: ['salesSummary', daysAgoISO(30), todayISO()],
    queryFn: () => getSalesSummary(daysAgoISO(30), todayISO()),
  });

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="card">
        <p className="text-sm text-surface-400">Total Products</p>
        <p className="mt-1 text-2xl font-semibold text-surface-600">{summary?.total_sales ?? 0}</p>
      </div>
      <div className="card">
        <p className="text-sm text-surface-400">Inventory Value</p>
        <p className="mt-1 text-2xl font-semibold text-surface-600">UGX {summary?.total_cost ?? 0}</p>
      </div>
      <div className="card">
        <p className="text-sm text-surface-400">Low Stock Items</p>
        <p className="mt-1 text-2xl font-semibold text-warning">0</p>
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

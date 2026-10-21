import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, Cell, LabelList, LineChart, Line, Pie, PieChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats } from '../api/dashboard';
import { getTopProducts, getDailySales, getSalesByPaymentMethod } from '../../reports/api/reports';
import { paymentMethodLabel } from '../../payments/lib/paymentMethods';
import { Card } from '../../../shared/ui/Card';
import { Spinner } from '../../../shared/ui/Spinner';
import { daysAgoISO, formatShortDate, monthStartISO, todayISO } from '../../../shared/utils/date';
import { formatMoney } from '../../../shared/utils/money';

const REFRESH_MS = 60_000;
const PAYMENT_COLORS = ['#0078d4', '#16a34a', '#9333ea', '#f59e0b'];

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardStats,
    refetchInterval: REFRESH_MS,
  });

  const today = todayISO();
  const thirtyDaysAgo = daysAgoISO(30);
  const dayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  const now = new Date();
  const monthName = now.toLocaleDateString('en-US', { month: 'long' });
  const monthStart = monthStartISO();

  const { data: topProducts } = useQuery({
    queryKey: ['topProducts', monthStart, today],
    queryFn: () => getTopProducts(monthStart, today),
    refetchInterval: REFRESH_MS,
  });

  const { data: dailySales } = useQuery({
    queryKey: ['dailySales', thirtyDaysAgo, today],
    queryFn: () => getDailySales(thirtyDaysAgo, today),
    refetchInterval: REFRESH_MS,
  });

  const { data: paymentMethods } = useQuery({
    queryKey: ['paymentMethods', thirtyDaysAgo, today],
    queryFn: () => getSalesByPaymentMethod(thirtyDaysAgo, today),
    refetchInterval: REFRESH_MS,
  });

  const paymentMix = useMemo(
    () =>
      (paymentMethods ?? []).map((entry) => ({
        method: entry.method,
        label: paymentMethodLabel(entry.method),
        count: entry.count,
        value: Number(entry.total),
      })),
    [paymentMethods],
  );

  const paymentTotal = useMemo(
    () => paymentMix.reduce((total, entry) => total + entry.value, 0),
    [paymentMix],
  );

  const salesTrend = useMemo(
    () =>
      (dailySales ?? []).map((day) => ({
        label: formatShortDate(day.date),
        date: day.date,
        sales: Number(day.total),
        transactions: day.transaction_count,
      })),
    [dailySales],
  );

  if (statsLoading) {
    return <Spinner className="h-64" />;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <StatCard title={`${dayName}'s Sales`} value={`${stats?.today_sales ?? 0}`} subtitle={`UGX ${stats?.today_revenue ?? 0}`} />
        <StatCard title="This Week" value={`${stats?.week_sales ?? 0}`} subtitle={`UGX ${stats?.week_revenue ?? 0}`} />
        <StatCard title={`${monthName}'s Sales`} value={`${stats?.month_sales ?? 0}`} subtitle={`UGX ${stats?.month_revenue ?? 0}`} />
        <StatCard title="Gross Profit" value={`UGX ${stats?.gross_profit ?? 0}`} subtitle={`Avg: UGX ${stats?.average_sale_value ?? 0}`} />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard title="Total Products" value={`${stats?.total_products ?? 0}`} />
        <StatCard title="Low Stock" value={`${stats?.low_stock_count ?? 0}`} warning />
        <StatCard title="Out of Stock" value={`${stats?.out_of_stock_count ?? 0}`} error />
      </div>

      <Card title="Sales Over Time" subtitle="Last 30 days">
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={salesTrend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} minTickGap={24} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              labelFormatter={(_, payload) => payload?.[0]?.payload?.date ?? ''}
              formatter={(value: number) => [formatMoney(value), 'Sales']}
            />
            <Line
              type="monotone"
              dataKey="sales"
              stroke="#0078d4"
              strokeWidth={2}
              dot={{ r: 3, fill: '#0078d4', strokeWidth: 0 }}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Payment Mix" subtitle="Last 30 days">
        {paymentMix.length === 0 ? (
          <p className="py-10 text-center text-sm text-surface-400">
            No paid sales in this period.
          </p>
        ) : (
          <div className="flex items-center gap-8">
            <div className="h-[220px] w-1/2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={paymentMix}
                    dataKey="value"
                    nameKey="label"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={2}
                  >
                    {paymentMix.map((entry, index) => (
                      <Cell
                        key={entry.method}
                        fill={PAYMENT_COLORS[index % PAYMENT_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [formatMoney(value), 'Sales']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-3">
              {paymentMix.map((entry, index) => (
                <div key={entry.method} className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{
                        backgroundColor: PAYMENT_COLORS[index % PAYMENT_COLORS.length],
                      }}
                    />
                    <div>
                      <p className="text-sm font-medium text-surface-600">{entry.label}</p>
                      <p className="text-xs text-surface-400">{entry.count} sales</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-surface-600">
                      {formatMoney(entry.value)}
                    </p>
                    <p className="text-xs text-surface-400">
                      {paymentTotal > 0 ? ((entry.value / paymentTotal) * 100).toFixed(1) : '0.0'}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card title="Top Products" subtitle={`Best sellers in ${monthName}`}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={(topProducts || []).slice(0, 5)} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="product_name" tick={{ fontSize: 12 }} width={170} interval={0} />
            <Tooltip formatter={(value: number) => [value, 'Units sold']} />
            <Bar dataKey="quantity_sold" fill="#0078d4">
              <LabelList dataKey="quantity_sold" position="right" fontSize={12} fill="#4b5563" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

function StatCard({ title, value, subtitle, warning, error }: { title: string; value: string; subtitle?: string; warning?: boolean; error?: boolean }) {
  return (
    <div className="card">
      <p className="text-sm text-surface-400">{title}</p>
      <p className={`mt-1 text-2xl font-semibold ${error ? 'text-error' : warning ? 'text-warning' : 'text-surface-600'}`}>
        {value}
      </p>
      {subtitle && <p className="mt-1 text-xs text-surface-400">{subtitle}</p>}
    </div>
  );
}


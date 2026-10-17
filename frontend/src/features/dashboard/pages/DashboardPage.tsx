import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats } from '../api/dashboard';
import { getTopProducts, getDailySales } from '../../reports/api/reports';
import { Card } from '../../../shared/ui/Card';
import { Spinner } from '../../../shared/ui/Spinner';

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardStats,
  });

  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const dayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  const now = new Date();
  const monthName = now.toLocaleDateString('en-US', { month: 'long' });
  const monthStart = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;

  const { data: topProducts } = useQuery({
    queryKey: ['topProducts', monthStart, today],
    queryFn: () => getTopProducts(monthStart, today),
  });

  const { data: dailySales } = useQuery({
    queryKey: ['dailySales', thirtyDaysAgo, today],
    queryFn: () => getDailySales(thirtyDaysAgo, today),
  });

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
          <LineChart data={dailySales || []}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="total" stroke="#0078d4" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Top Products" subtitle={`Best sellers in ${monthName}`}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={(topProducts || []).slice(0, 5)} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e1dfdd" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="product_name" tick={{ fontSize: 12 }} width={170} interval={0} />
            <Tooltip />
            <Bar dataKey="quantity_sold" fill="#0078d4" />
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

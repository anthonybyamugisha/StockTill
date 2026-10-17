import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDailySales, getSalesSummary, getTopProducts } from '../api/reports';

export function ReportsPage() {
  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const { data: summary } = useQuery({
    queryKey: ['salesSummary', thirtyDaysAgo, today],
    queryFn: () => getSalesSummary(thirtyDaysAgo, today),
  });

  const { data: dailySales } = useQuery({
    queryKey: ['dailySales', thirtyDaysAgo, today],
    queryFn: () => getDailySales(thirtyDaysAgo, today),
  });

  const { data: topProducts } = useQuery({
    queryKey: ['topProducts', thirtyDaysAgo, today],
    queryFn: () => getTopProducts(thirtyDaysAgo, today),
  });

  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-bold">Reports</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Total Sales</p>
          <p className="text-2xl font-bold">{summary?.total_sales ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Revenue</p>
          <p className="text-2xl font-bold">UGX {summary?.total_revenue ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Gross Profit</p>
          <p className="text-2xl font-bold">UGX {summary?.gross_profit ?? 0}</p>
        </div>
      </div>
      <div className="mt-6">
        <h2 className="mb-2 text-lg font-semibold">Sales Over Time</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dailySales ?? []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="total" stroke="#2563eb" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-6">
        <h2 className="mb-2 text-lg font-semibold">Top Products</h2>
        <ul className="space-y-1">
          {topProducts?.map((p) => (
            <li key={p.product_id} className="flex justify-between border-b py-1">
              <span>{p.product_name}</span>
              <span>{p.quantity_sold} sold</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

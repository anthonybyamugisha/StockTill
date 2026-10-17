import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '../api/dashboard';

export function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardStats,
  });

  if (isLoading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Today's Sales</p>
          <p className="text-2xl font-bold">{stats?.today_sales ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">This Week</p>
          <p className="text-2xl font-bold">{stats?.week_sales ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">This Month</p>
          <p className="text-2xl font-bold">{stats?.month_sales ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Avg Sale Value</p>
          <p className="text-2xl font-bold">UGX {stats?.average_sale_value ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Total Products</p>
          <p className="text-2xl font-bold">{stats?.total_products ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Low Stock</p>
          <p className="text-2xl font-bold">{stats?.low_stock_count ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Out of Stock</p>
          <p className="text-2xl font-bold">{stats?.out_of_stock_count ?? 0}</p>
        </div>
        <div className="rounded border p-4">
          <p className="text-sm text-gray-500">Gross Profit</p>
          <p className="text-2xl font-bold">UGX {stats?.gross_profit ?? 0}</p>
        </div>
      </div>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { listSales } from '../api/sales';

export function SalesPage() {
  const { data: sales, isLoading } = useQuery({ queryKey: ['sales'], queryFn: listSales });

  if (isLoading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-bold">Sales</h1>
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2">Receipt</th>
            <th className="py-2">Status</th>
            <th className="py-2">Total</th>
            <th className="py-2">Date</th>
          </tr>
        </thead>
        <tbody>
          {sales?.map((s) => (
            <tr key={s.id} className="border-b">
              <td className="py-2">{s.receipt_number}</td>
              <td className="py-2">{s.status}</td>
              <td className="py-2">UGX {s.total}</td>
              <td className="py-2">{new Date(s.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

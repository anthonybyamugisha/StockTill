import { useQuery } from '@tanstack/react-query';
import { listProducts } from '../api/catalog';

export function CatalogPage() {
  const { data: products, isLoading } = useQuery({
    queryKey: ['products'],
    queryFn: listProducts,
  });

  if (isLoading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-bold">Catalog</h1>
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2">Name</th>
            <th className="py-2">SKU</th>
            <th className="py-2">Price</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {products?.map((p) => (
            <tr key={p.id} className="border-b">
              <td className="py-2">{p.name}</td>
              <td className="py-2">{p.sku}</td>
              <td className="py-2">UGX {p.selling_price}</td>
              <td className="py-2">{p.is_active ? 'Active' : 'Inactive'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

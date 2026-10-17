import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchProducts } from '../api/pos';

interface ProductSearchProps {
  onAddToCart: (product: {
    product_id: string;
    name: string;
    unit_price: string;
    unit_cost: string;
  }) => void;
}

export function ProductSearch({ onAddToCart }: ProductSearchProps) {
  const [query, setQuery] = useState('');
  const { data: products, isLoading } = useQuery({
    queryKey: ['productSearch', query],
    queryFn: () => searchProducts(query),
    enabled: query.length >= 2,
  });

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by name, SKU or barcode..."
        className="w-full rounded border border-gray-300 px-3 py-2"
      />
      {isLoading && <p className="mt-2 text-sm text-gray-500">Searching...</p>}
      {products && (
        <ul className="mt-2 divide-y">
          {products.map((p: { id: string; name: string; selling_price: string; buying_cost: string }) => (
            <li key={p.id} className="flex items-center justify-between py-2">
              <span>{p.name}</span>
              <button
                onClick={() =>
                  onAddToCart({
                    product_id: p.id,
                    name: p.name,
                    unit_price: p.selling_price,
                    unit_cost: p.buying_cost,
                  })
                }
                className="rounded bg-blue-600 px-3 py-1 text-sm text-white"
              >
                Add
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

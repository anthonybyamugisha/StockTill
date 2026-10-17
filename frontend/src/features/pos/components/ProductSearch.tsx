import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchProducts } from '../api/pos';

interface ProductSearchProps {
  onAddToCart: (product: {
    product_id: string;
    name: string;
    unit_price: string;
    unit_cost: string;
  }) => void;
  onScan?: (code: string) => void;
}

const LOOKS_LIKE_BARCODE = /^[0-9A-Za-z._-]{6,}$/;

export function ProductSearch({ onAddToCart, onScan }: ProductSearchProps) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const id = setTimeout(() => setDebouncedQuery(query.trim()), 300);
    return () => clearTimeout(id);
  }, [query]);

  const { data: products, isLoading } = useQuery({
    queryKey: ['productSearch', debouncedQuery],
    queryFn: () => searchProducts(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== 'Enter') return;
    const code = event.currentTarget.value.trim();
    if (code && LOOKS_LIKE_BARCODE.test(code) && onScan) {
      event.preventDefault();
      onScan(code);
      setQuery('');
    }
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search by name, SKU or barcode..."
        className="w-full rounded border border-gray-300 px-3 py-2"
      />
      {isLoading && <p className="mt-2 text-sm text-gray-500">Searching...</p>}
      {products && products.length > 0 && (
        <ul className="mt-2 divide-y">
          {products.map((p) => (
            <li key={p.id} className="flex items-center justify-between py-2">
              <span>
                {p.name}
                {p.sku && <span className="ml-2 text-xs text-gray-400">{p.sku}</span>}
              </span>
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
      {products && products.length === 0 && debouncedQuery.length >= 2 && (
        <p className="mt-2 text-sm text-gray-500">No products match "{debouncedQuery}".</p>
      )}
    </div>
  );
}

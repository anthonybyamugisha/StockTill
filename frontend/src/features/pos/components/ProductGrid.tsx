import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listAvailableProducts, listCategories, ProductLookup } from '../api/pos';
import { filterProducts } from '../lib/productFilter';
import { listStockItems } from '../../inventory/api/inventory';
import { formatMoney } from '../../../shared/utils/money';

interface ProductGridProps {
  onSelect: (product: ProductLookup) => void;
  onScan?: (code: string) => void;
}

const LOOKS_LIKE_BARCODE = /^[0-9A-Za-z._-]{6,}$/;

export function ProductGrid({ onSelect, onScan }: ProductGridProps) {
  const [query, setQuery] = useState('');
  const [categoryId, setCategoryId] = useState<string | null>(null);

  const { data: products = [], isLoading } = useQuery({
    queryKey: ['pos-products'],
    queryFn: () => listAvailableProducts(),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['pos-categories'],
    queryFn: listCategories,
  });

  const { data: stockItems = [] } = useQuery({
    queryKey: ['stockItems'],
    queryFn: listStockItems,
  });

  const stockById = useMemo(
    () => new Map(stockItems.map((item) => [item.product_id, item.available_quantity])),
    [stockItems],
  );

  const visible = useMemo(
    () => filterProducts(products, query, categoryId),
    [products, query, categoryId],
  );

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
    <div className="space-y-3">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search products by name, SKU or barcode, or tap an item below..."
        className="input"
        aria-label="Search products"
      />

      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <CategoryChip
            label="All"
            active={categoryId === null}
            onClick={() => setCategoryId(null)}
          />
          {categories.map((category) => (
            <CategoryChip
              key={category.id}
              label={category.name}
              active={categoryId === category.id}
              onClick={() => setCategoryId(category.id)}
            />
          ))}
        </div>
      )}

      {isLoading ? (
        <p className="py-8 text-center text-sm text-surface-400">Loading products...</p>
      ) : products.length === 0 ? (
        <p className="py-8 text-center text-sm text-surface-400">
          No products yet. Add products in the Catalog first.
        </p>
      ) : visible.length === 0 ? (
        <p className="py-8 text-center text-sm text-surface-400">
          No products match your search.
        </p>
      ) : (
        <>
          <p className="text-xs text-surface-400">
            {visible.length} product{visible.length === 1 ? '' : 's'} &#8212; tap one to add it to the
            sale.
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
            {visible.map((product) => {
              const available = stockById.get(product.id) ?? 0;
              const outOfStock = available <= 0;
              return (
                <button
                  key={product.id}
                  type="button"
                  onClick={() => onSelect(product)}
                  disabled={outOfStock}
                  className="flex min-h-[5.5rem] flex-col justify-between rounded-lg border border-surface-200 bg-white p-3 text-left transition-colors hover:border-primary-500 hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-surface-200 disabled:hover:bg-white"
                  title={product.name}
                >
                  <span className="line-clamp-2 text-sm font-medium text-surface-600">
                    {product.name}
                  </span>
                  <span className="mt-2 flex items-baseline justify-between gap-2">
                    <span className="text-sm font-semibold text-primary-600">
                      {formatMoney(product.selling_price)}
                    </span>
                    <span
                      className={`text-xs ${outOfStock ? 'text-error' : 'text-surface-400'}`}
                    >
                      {outOfStock ? 'Out of stock' : `${available} left`}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

interface CategoryChipProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

function CategoryChip({ label, active, onClick }: CategoryChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-sm font-medium transition-colors ${
        active
          ? 'border-primary-500 bg-primary-500 text-white'
          : 'border-surface-200 bg-white text-surface-600 hover:bg-surface-50'
      }`}
    >
      {label}
    </button>
  );
}

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listCategories,
  listProducts,
  createProduct,
  updateProduct,
  deactivateProduct,
  Product,
} from '../api/catalog';
import { adjustStock, listStockItems, StockItem } from '../../inventory/api/inventory';
import { AdjustStockModal } from '../../inventory/components/AdjustStockModal';
import { CategoryManager } from '../components/CategoryManager';
import { ProductModal } from '../components/ProductModal';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';
import { matchesProductQuery } from '../../../shared/utils/productSearch';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';

export function CatalogPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'products' | 'categories'>('products');
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [productToDeactivate, setProductToDeactivate] = useState<Product | null>(null);
  const [stockProduct, setStockProduct] = useState<Product | null>(null);

  const { data: products, isLoading } = useQuery({
    queryKey: ['catalog-products'],
    queryFn: () => listProducts({ activeOnly: false }),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['catalog-categories'],
    queryFn: () => listCategories(false),
  });

  const { data: stockItems = [] } = useQuery({
    queryKey: ['stockItems'],
    queryFn: listStockItems,
  });

  const stockByProduct = useMemo(
    () => new Map<string, StockItem>(stockItems.map((item) => [item.product_id, item])),
    [stockItems],
  );

  const categoryNames = useMemo(
    () => new Map(categories.map((category) => [category.id, category.name])),
    [categories],
  );

  const visible = useMemo(
    () =>
      (products ?? []).filter(
        (product) =>
          matchesProductQuery(product, search) &&
          (!categoryFilter || product.category_id === categoryFilter),
      ),
    [products, search, categoryFilter],
  );

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['catalog-products'] });
    queryClient.invalidateQueries({ queryKey: ['products'] });
  };

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: (product) => {
      refresh();
      setShowModal(false);
      toast.success(`Product "${product.name}" added successfully`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Product> }) => updateProduct(id, data),
    onSuccess: (product) => {
      refresh();
      setShowModal(false);
      toast.success(`Product "${product.name}" updated`);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateProduct,
    onSuccess: () => {
      refresh();
      toast.success(`Product "${productToDeactivate?.name ?? ''}" deactivated`);
      setProductToDeactivate(null);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not deactivate product')),
  });

  const reactivateMutation = useMutation({
    mutationFn: (id: string) => updateProduct(id, { is_active: true }),
    onSuccess: (product) => {
      refresh();
      toast.success(`Product "${product.name}" is active again`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not reactivate product')),
  });

  const adjustMutation = useMutation({
    mutationFn: adjustStock,
    onSuccess: (movement, variables) => {
      queryClient.invalidateQueries({ queryKey: ['stockItems'] });
      queryClient.invalidateQueries({ queryKey: ['lowStock'] });
      queryClient.invalidateQueries({ queryKey: ['outOfStock'] });
      setStockProduct(null);
      const removed =
        variables.movement_type === 'adjustment_out' || variables.movement_type === 'write_off';
      const name = products?.find((product) => product.id === variables.product_id)?.name;
      toast.success(
        `Stock ${removed ? 'reduced' : 'increased'} by ${Math.abs(movement.quantity)} for "${
          name ?? 'product'
        }"`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not adjust stock')),
  });

  const columns = [
    {
      key: 'name',
      header: 'Product',
      render: (p: Product) => (
        <div className="flex items-center gap-3">
          {p.image_url ? (
            <img
              src={p.image_url}
              alt=""
              className="h-10 w-10 rounded border border-surface-100 object-cover"
            />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded border border-surface-100 bg-surface-50 text-xs text-surface-400">
              No img
            </div>
          )}
          <div>
            <p className="font-medium">{p.name}</p>
            <p className="text-xs text-surface-400">{p.sku}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      render: (p: Product) =>
        (p.category_id && categoryNames.get(p.category_id)) ?? '—',
    },
    { key: 'price', header: 'Price', render: (p: Product) => `UGX ${p.selling_price}` },
    { key: 'cost', header: 'Cost', render: (p: Product) => `UGX ${p.buying_cost}` },
    {
      key: 'margin',
      header: 'Margin',
      render: (p: Product) => {
        const margin = parseFloat(p.selling_price) - parseFloat(p.buying_cost);
        return `UGX ${margin.toFixed(2)}`;
      },
    },
    {
      key: 'stock',
      header: 'Stock',
      render: (p: Product) => {
        const quantity = stockByProduct.get(p.id)?.quantity_on_hand ?? 0;
        const variant =
          quantity === 0 ? 'error' : quantity <= p.minimum_stock_level ? 'warning' : 'success';
        return <Badge variant={variant}>{quantity}</Badge>;
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (p: Product) => (
        <Badge variant={p.is_active ? 'success' : 'neutral'}>
          {p.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (p: Product) => (
        <div className="flex gap-1">
          <button
            onClick={() => {
              setEditingProduct(p);
              setShowModal(true);
            }}
            className="btn-ghost btn-sm"
          >
            Edit
          </button>
          <button onClick={() => setStockProduct(p)} className="btn-ghost btn-sm">
            Stock
          </button>
          {p.is_active ? (
            <button onClick={() => setProductToDeactivate(p)} className="btn-danger btn-sm">
              Deactivate
            </button>
          ) : (
            <button
              onClick={() => reactivateMutation.mutate(p.id)}
              disabled={reactivateMutation.isPending}
              className="btn-secondary btn-sm"
            >
              Reactivate
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="inline-flex rounded-md border border-surface-200 bg-white p-1">
          <button
            onClick={() => setTab('products')}
            className={`rounded px-4 py-1.5 text-sm font-medium ${
              tab === 'products'
                ? 'bg-primary-500 text-white'
                : 'text-surface-500 hover:bg-surface-50'
            }`}
          >
            Products
          </button>
          <button
            onClick={() => setTab('categories')}
            className={`rounded px-4 py-1.5 text-sm font-medium ${
              tab === 'categories'
                ? 'bg-primary-500 text-white'
                : 'text-surface-500 hover:bg-surface-50'
            }`}
          >
            Categories
          </button>
        </div>
        {tab === 'products' && (
          <Button
            onClick={() => {
              setEditingProduct(null);
              setShowModal(true);
            }}
          >
            Add Product
          </Button>
        )}
      </div>

      {tab === 'categories' ? (
        <CategoryManager />
      ) : (
        <>
          <div className="flex items-center gap-3">
            <div className="relative w-80">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products..."
                className="input pl-10"
              />
              <svg
                className="absolute left-3 top-2.5 h-4 w-4 text-surface-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input w-56"
            >
              <option value="">All categories</option>
              {categories
                .filter((category) => category.is_active)
                .map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
            </select>
          </div>

          <Card>
            {isLoading ? (
              <p className="py-8 text-center text-surface-400">Loading products...</p>
            ) : (
              <>
                {(search.trim() || categoryFilter) && (
                  <p className="mb-3 text-xs text-surface-400">
                    {visible.length} of {products?.length ?? 0} product
                    {(products?.length ?? 0) === 1 ? '' : 's'} match
                  </p>
                )}
                <Table
                  columns={columns}
                  data={visible}
                  keyExtractor={(p) => p.id}
                  emptyMessage={
                    search.trim() || categoryFilter
                      ? 'No products match your filters'
                      : 'No products found'
                  }
                />
              </>
            )}
          </Card>
        </>
      )}

      {showModal && (
        <ProductModal
          product={editingProduct}
          categories={categories}
          error={extractError(createMutation.error ?? updateMutation.error)}
          onClose={() => {
            createMutation.reset();
            updateMutation.reset();
            setShowModal(false);
          }}
          onSubmit={(data) => {
            if (editingProduct) {
              updateMutation.mutate({ id: editingProduct.id, data });
            } else {
              createMutation.mutate(data);
            }
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {stockProduct && (
        <AdjustStockModal
          products={products ?? []}
          initialProductId={stockProduct.id}
          lockProduct
          onClose={() => setStockProduct(null)}
          onSubmit={(data) => adjustMutation.mutate(data)}
          isLoading={adjustMutation.isPending}
        />
      )}

      <ConfirmDialog
        isOpen={productToDeactivate !== null}
        title="Deactivate product?"
        message={
          <>
            <p>
              Are you sure you want to deactivate{' '}
              <span className="font-medium text-surface-700">{productToDeactivate?.name}</span>?
            </p>
            <p className="mt-2">
              It will no longer appear in the POS and cannot be sold. Its stock history and past
              sales are kept, and you can reactivate it later.
            </p>
          </>
        }
        confirmLabel="Yes, deactivate"
        cancelLabel="Keep active"
        isLoading={deactivateMutation.isPending}
        onConfirm={() => {
          if (productToDeactivate) deactivateMutation.mutate(productToDeactivate.id);
        }}
        onCancel={() => {
          deactivateMutation.reset();
          setProductToDeactivate(null);
        }}
      />
    </div>
  );
}

function extractError(error: unknown): string | null {
  if (!error) return null;
  const response = (error as { response?: { data?: unknown; statusText?: string } }).response;
  const data = response?.data;
  if (typeof data === 'string') return data;
  if (data && typeof data === 'object') {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length > 0) {
      const [field, value] = entries[0];
      const message = Array.isArray(value) ? value[0] : value;
      return field === 'detail' ? String(message) : `${field}: ${message}`;
    }
  }
  return response?.statusText ?? 'Could not save product';
}

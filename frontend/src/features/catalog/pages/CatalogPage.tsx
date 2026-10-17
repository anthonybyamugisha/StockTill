import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listProducts, createProduct, updateProduct, deactivateProduct, Product } from '../api/catalog';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Modal } from '../../../shared/ui/Modal';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { Input } from '../../../shared/ui/Input';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';
import { matchesProductQuery } from '../../../shared/utils/productSearch';

export function CatalogPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [productToDeactivate, setProductToDeactivate] = useState<Product | null>(null);

  const { data: products, isLoading } = useQuery({
    queryKey: ['catalog-products'],
    queryFn: () => listProducts({ activeOnly: false }),
  });

  const visible = useMemo(
    () => (products ?? []).filter((product) => matchesProductQuery(product, search)),
    [products, search],
  );

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['catalog-products'] });
    queryClient.invalidateQueries({ queryKey: ['products'] });
  };

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      refresh();
      setShowModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Product> }) => updateProduct(id, data),
    onSuccess: () => {
      refresh();
      setShowModal(false);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateProduct,
    onSuccess: () => {
      refresh();
      setProductToDeactivate(null);
    },
  });

  const reactivateMutation = useMutation({
    mutationFn: (id: string) => updateProduct(id, { is_active: true }),
    onSuccess: refresh,
  });

  const columns = [
    { key: 'name', header: 'Product', render: (p: Product) => (
      <div>
        <p className="font-medium">{p.name}</p>
        <p className="text-xs text-surface-400">{p.sku}</p>
      </div>
    )},
    { key: 'price', header: 'Price', render: (p: Product) => `UGX ${p.selling_price}` },
    { key: 'cost', header: 'Cost', render: (p: Product) => `UGX ${p.buying_cost}` },
    { key: 'margin', header: 'Margin', render: (p: Product) => {
      const margin = parseFloat(p.selling_price) - parseFloat(p.buying_cost);
      return `UGX ${margin.toFixed(2)}`;
    }},
    { key: 'status', header: 'Status', render: (p: Product) => (
      <Badge variant={p.is_active ? 'success' : 'neutral'}>{p.is_active ? 'Active' : 'Inactive'}</Badge>
    )},
    { key: 'actions', header: '', render: (p: Product) => (
      <div className="flex gap-1">
        <button onClick={() => { setEditingProduct(p); setShowModal(true); }} className="btn-ghost btn-sm">
          Edit
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
    )},
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-80">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search products..."
            className="input pl-10"
          />
          <svg className="absolute left-3 top-2.5 h-4 w-4 text-surface-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <Button onClick={() => { setEditingProduct(null); setShowModal(true); }}>
          Add Product
        </Button>
      </div>

      <Card>
        {isLoading ? (
          <p className="py-8 text-center text-surface-400">Loading products...</p>
        ) : (
          <>
            {search.trim() && (
              <p className="mb-3 text-xs text-surface-400">
                {visible.length} of {products?.length ?? 0} product
                {(products?.length ?? 0) === 1 ? '' : 's'} match &ldquo;{search.trim()}&rdquo;
              </p>
            )}
            <Table
              columns={columns}
              data={visible}
              keyExtractor={(p) => p.id}
              emptyMessage={search.trim() ? 'No products match your search' : 'No products found'}
            />
          </>
        )}
      </Card>

      {showModal && (
        <ProductModal
          product={editingProduct}
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
              It will no longer appear in the POS and cannot be sold. Its stock history and past sales
              are kept, and you can reactivate it later.
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

function ProductModal({ product, error, onClose, onSubmit, isLoading }: {
  product: Product | null;
  error: string | null;
  onClose: () => void;
  onSubmit: (data: Partial<Product> & { opening_stock?: number }) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState({
    name: product?.name || '',
    sku: product?.sku || '',
    description: product?.description || '',
    selling_price: product?.selling_price || '',
    buying_cost: product?.buying_cost || '',
    barcode: product?.barcode || '',
    minimum_stock_level: product?.minimum_stock_level || 0,
    category_id: product?.category_id || '',
    opening_stock: 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Partial<Product> & { opening_stock?: number } = {
      name: form.name,
      sku: form.sku,
      selling_price: form.selling_price,
      buying_cost: form.buying_cost,
      description: form.description,
      minimum_stock_level: Number.isFinite(Number(form.minimum_stock_level))
        ? Number(form.minimum_stock_level)
        : 0,
    };
    if (form.barcode) payload.barcode = form.barcode;
    if (form.category_id) payload.category_id = form.category_id;
    if (!product && Number(form.opening_stock) > 0) {
      payload.opening_stock = Number(form.opening_stock);
    }
    onSubmit(payload);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={product ? 'Edit Product' : 'Add Product'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        {error && (
          <p role="alert" className="col-span-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <Input label="SKU" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} required />
        <Input label="Selling Price" type="number" step="0.01" value={form.selling_price} onChange={(e) => setForm({ ...form, selling_price: e.target.value })} required />
        <Input label="Buying Cost" type="number" step="0.01" value={form.buying_cost} onChange={(e) => setForm({ ...form, buying_cost: e.target.value })} required />
        <Input label="Barcode" value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} />
        <Input label="Min Stock Level" type="number" value={form.minimum_stock_level} onChange={(e) => setForm({ ...form, minimum_stock_level: parseInt(e.target.value) })} />
        {!product && (
          <Input
            label="Opening Stock"
            type="number"
            min="0"
            value={form.opening_stock}
            onChange={(e) => setForm({ ...form, opening_stock: parseInt(e.target.value) || 0 })}
          />
        )}
        <div className="col-span-2">
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
      </form>
    </Modal>
  );
}

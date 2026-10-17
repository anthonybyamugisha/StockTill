import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listProducts, createProduct, updateProduct, deactivateProduct } from '../api/catalog';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Modal } from '../../../shared/ui/Modal';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
import { Table } from '../../../shared/ui/Table';
import { Badge } from '../../../shared/ui/Badge';

export function CatalogPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<any>(null);

  const { data: products, isLoading } = useQuery({
    queryKey: ['products', search],
    queryFn: () => listProducts(),
  });

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setShowModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      setShowModal(false);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateProduct,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
  });

  const columns = [
    { key: 'name', header: 'Product', render: (p: any) => (
      <div>
        <p className="font-medium">{p.name}</p>
        <p className="text-xs text-surface-400">{p.sku}</p>
      </div>
    )},
    { key: 'price', header: 'Price', render: (p: any) => `UGX ${p.selling_price}` },
    { key: 'cost', header: 'Cost', render: (p: any) => `UGX ${p.buying_cost}` },
    { key: 'margin', header: 'Margin', render: (p: any) => {
      const margin = parseFloat(p.selling_price) - parseFloat(p.buying_cost);
      return `UGX ${margin.toFixed(2)}`;
    }},
    { key: 'status', header: 'Status', render: (p: any) => (
      <Badge variant={p.is_active ? 'success' : 'neutral'}>{p.is_active ? 'Active' : 'Inactive'}</Badge>
    )},
    { key: 'actions', header: '', render: (p: any) => (
      <div className="flex gap-1">
        <button onClick={() => { setEditingProduct(p); setShowModal(true); }} className="btn-ghost btn-sm">
          Edit
        </button>
        {p.is_active && (
          <button onClick={() => deactivateMutation.mutate(p.id)} className="btn-danger btn-sm">
            Deactivate
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
          <Table
            columns={columns}
            data={products || []}
            keyExtractor={(p) => p.id}
            emptyMessage="No products found"
          />
        )}
      </Card>

      {showModal && (
        <ProductModal
          product={editingProduct}
          onClose={() => setShowModal(false)}
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
    </div>
  );
}

function ProductModal({ product, onClose, onSubmit, isLoading }: {
  product: any;
  onClose: () => void;
  onSubmit: (data: any) => void;
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
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
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
        <Input label="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <Input label="SKU" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} required />
        <Input label="Selling Price" type="number" step="0.01" value={form.selling_price} onChange={(e) => setForm({ ...form, selling_price: e.target.value })} required />
        <Input label="Buying Cost" type="number" step="0.01" value={form.buying_cost} onChange={(e) => setForm({ ...form, buying_cost: e.target.value })} required />
        <Input label="Barcode" value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} />
        <Input label="Min Stock Level" type="number" value={form.minimum_stock_level} onChange={(e) => setForm({ ...form, minimum_stock_level: parseInt(e.target.value) })} />
        <div className="col-span-2">
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
      </form>
    </Modal>
  );
}

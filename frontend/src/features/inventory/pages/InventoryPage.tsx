import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLowStock, getOutOfStock, adjustStock } from '../api/inventory';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { Modal } from '../../../shared/ui/Modal';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
import { listProducts } from '../../catalog/api/catalog';

export function InventoryPage() {
  const queryClient = useQueryClient();
  const [showAdjustModal, setShowAdjustModal] = useState(false);

  const { data: lowStock } = useQuery({ queryKey: ['lowStock'], queryFn: getLowStock });
  const { data: outOfStock } = useQuery({ queryKey: ['outOfStock'], queryFn: getOutOfStock });

  const adjustMutation = useMutation({
    mutationFn: adjustStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lowStock'] });
      queryClient.invalidateQueries({ queryKey: ['outOfStock'] });
      setShowAdjustModal(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-surface-400">Low Stock Alerts</p>
          <p className="mt-1 text-2xl font-semibold text-warning">{lowStock?.length ?? 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Out of Stock</p>
          <p className="mt-1 text-2xl font-semibold text-error">{outOfStock?.length ?? 0}</p>
        </div>
        <div className="card flex items-center justify-end">
          <Button onClick={() => setShowAdjustModal(true)}>Adjust Stock</Button>
        </div>
      </div>

      <Card title="Low Stock Products">
        <Table
          columns={[
            { key: 'product', header: 'Product', render: (item: any) => (
              <div>
                <p className="font-medium">Product {item.product_id.slice(0, 8)}</p>
                <p className="text-xs text-surface-400">ID: {item.product_id.slice(0, 8)}</p>
              </div>
            )},
            { key: 'quantity', header: 'In Stock', render: (item: any) => <Badge variant="warning">{item.quantity_on_hand}</Badge> },
            { key: 'status', header: 'Status', render: () => <Badge variant="warning">Low Stock</Badge> },
          ]}
          data={lowStock || []}
          keyExtractor={(item) => item.product_id}
          emptyMessage="No low stock products"
        />
      </Card>

      <Card title="Out of Stock Products">
        <Table
          columns={[
            { key: 'product', header: 'Product', render: (item: any) => (
              <p className="font-medium">Product {item.product_id.slice(0, 8)}</p>
            )},
            { key: 'status', header: 'Status', render: () => <Badge variant="error">Out of Stock</Badge> },
          ]}
          data={outOfStock || []}
          keyExtractor={(item) => item.product_id}
          emptyMessage="No out of stock products"
        />
      </Card>

      {showAdjustModal && (
        <AdjustStockModal
          onClose={() => setShowAdjustModal(false)}
          onSubmit={(data) => adjustMutation.mutate(data)}
          isLoading={adjustMutation.isPending}
        />
      )}
    </div>
  );
}

function AdjustStockModal({ onClose, onSubmit, isLoading }: {
  onClose: () => void;
  onSubmit: (data: any) => void;
  isLoading: boolean;
}) {
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: listProducts });
  const [form, setForm] = useState({
    product_id: '',
    quantity: 1,
    movement_type: 'adjustment_in',
    reason: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Adjust Stock"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isLoading}>{isLoading ? 'Saving...' : 'Save'}</Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Select
          label="Product"
          value={form.product_id}
          onChange={(e) => setForm({ ...form, product_id: e.target.value })}
          options={(products || []).map((p: any) => ({ value: p.id, label: p.name }))}
        />
        <Select
          label="Movement Type"
          value={form.movement_type}
          onChange={(e) => setForm({ ...form, movement_type: e.target.value })}
          options={[
            { value: 'adjustment_in', label: 'Adjustment In' },
            { value: 'adjustment_out', label: 'Adjustment Out' },
            { value: 'opening', label: 'Opening Stock' },
            { value: 'purchase', label: 'Purchase' },
            { value: 'write_off', label: 'Write Off' },
          ]}
        />
        <Input label="Quantity" type="number" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) })} />
        <Input label="Reason" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} required />
      </form>
    </Modal>
  );
}

import { useState } from 'react';
import { AdjustStockRequest } from '../api/inventory';
import { Product } from '../../catalog/api/catalog';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { Modal } from '../../../shared/ui/Modal';
import { Select } from '../../../shared/ui/Select';

export function AdjustStockModal({
  products,
  initialProductId = '',
  lockProduct = false,
  onClose,
  onSubmit,
  isLoading,
}: {
  products: Product[];
  initialProductId?: string;
  lockProduct?: boolean;
  onClose: () => void;
  onSubmit: (data: AdjustStockRequest) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState<AdjustStockRequest>({
    product_id: initialProductId,
    quantity: 1,
    movement_type: 'adjustment_in',
    reason: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const productOptions = lockProduct
    ? [
        {
          value: initialProductId,
          label: products.find((p) => p.id === initialProductId)?.name ?? 'Product',
        },
      ]
    : products.map((p) => ({ value: p.id, label: p.name }));

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Adjust Stock"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !form.product_id}>
            {isLoading ? 'Saving...' : 'Save'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Select
          label="Product"
          value={form.product_id}
          onChange={(e) => setForm({ ...form, product_id: e.target.value })}
          options={[{ value: '', label: 'Select a product' }, ...productOptions]}
          disabled={lockProduct}
          required
        />
        <Select
          label="Movement Type"
          value={form.movement_type}
          onChange={(e) => setForm({ ...form, movement_type: e.target.value })}
          options={[
            { value: 'adjustment_in', label: 'Add stock' },
            { value: 'adjustment_out', label: 'Remove stock' },
            { value: 'opening', label: 'Opening stock' },
            { value: 'purchase', label: 'Purchase' },
            { value: 'write_off', label: 'Write off' },
          ]}
        />
        <Input
          label="Quantity"
          type="number"
          min="1"
          value={form.quantity}
          onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) || 0 })}
          required
        />
        <Input
          label="Reason"
          value={form.reason}
          onChange={(e) => setForm({ ...form, reason: e.target.value })}
          required
        />
        <Input
          label="Reference (optional)"
          value={form.reference ?? ''}
          onChange={(e) => setForm({ ...form, reference: e.target.value || undefined })}
        />
      </form>
    </Modal>
  );
}

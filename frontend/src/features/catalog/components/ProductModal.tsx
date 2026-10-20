import { useState } from 'react';
import { Category, Product } from '../api/catalog';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { Modal } from '../../../shared/ui/Modal';
import { Select } from '../../../shared/ui/Select';

type ProductPayload = Partial<Product> & { opening_stock?: number };

export function ProductModal({
  product,
  categories,
  error,
  onClose,
  onSubmit,
  isLoading,
}: {
  product: Product | null;
  categories: Category[];
  error: string | null;
  onClose: () => void;
  onSubmit: (data: ProductPayload) => void;
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
    image_url: product?.image_url || '',
    opening_stock: 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: ProductPayload = {
      name: form.name,
      sku: form.sku,
      selling_price: form.selling_price,
      buying_cost: form.buying_cost,
      description: form.description,
      barcode: form.barcode.trim() || null,
      category_id: form.category_id || null,
      image_url: form.image_url.trim() || null,
      minimum_stock_level: Number.isFinite(Number(form.minimum_stock_level))
        ? Number(form.minimum_stock_level)
        : 0,
    };
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
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
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
        <Input
          label="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <Input
          label="SKU"
          value={form.sku}
          onChange={(e) => setForm({ ...form, sku: e.target.value })}
          required
        />
        <Input
          label="Selling Price"
          type="number"
          step="0.01"
          min="0"
          value={form.selling_price}
          onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
          required
        />
        <Input
          label="Buying Cost"
          type="number"
          step="0.01"
          min="0"
          value={form.buying_cost}
          onChange={(e) => setForm({ ...form, buying_cost: e.target.value })}
          required
        />
        <Input
          label="Barcode"
          value={form.barcode}
          onChange={(e) => setForm({ ...form, barcode: e.target.value })}
        />
        <Select
          label="Category"
          value={form.category_id}
          onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          options={[
            { value: '', label: 'No category' },
            ...categories
              .filter((category) => category.is_active || category.id === product?.category_id)
              .map((category) => ({ value: category.id, label: category.name })),
          ]}
        />
        <Input
          label="Min Stock Level"
          type="number"
          min="0"
          value={form.minimum_stock_level}
          onChange={(e) =>
            setForm({ ...form, minimum_stock_level: parseInt(e.target.value) || 0 })
          }
        />
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
          <Input
            label="Image URL"
            type="url"
            placeholder="https://example.com/product.jpg"
            value={form.image_url}
            onChange={(e) => setForm({ ...form, image_url: e.target.value })}
          />
        </div>
        {form.image_url.trim() && (
          <div className="col-span-2 flex items-center gap-3 rounded-md border border-surface-100 p-3">
            <img
              src={form.image_url}
              alt="Product preview"
              className="h-16 w-16 rounded object-cover"
            />
            <p className="text-xs text-surface-400">Image preview</p>
          </div>
        )}
        <div className="col-span-2">
          <Input
            label="Description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
      </form>
    </Modal>
  );
}

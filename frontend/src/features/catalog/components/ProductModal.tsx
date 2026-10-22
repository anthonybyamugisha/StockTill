import { useState } from 'react';
import { Category, Product } from '../api/catalog';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { Modal } from '../../../shared/ui/Modal';
import { Select } from '../../../shared/ui/Select';
import { imageFileToDataUrl } from '../../../shared/utils/image';

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
  const [imageError, setImageError] = useState<string | null>(null);
  const [isPreparingImage, setIsPreparingImage] = useState(false);
  const imageFromDevice = form.image_url.startsWith('data:image/');

  const handleImageFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setImageError(null);
    setIsPreparingImage(true);
    try {
      const dataUrl = await imageFileToDataUrl(file);
      setForm((current) => ({ ...current, image_url: dataUrl }));
    } catch (error) {
      setImageError(error instanceof Error ? error.message : 'Could not read that image.');
    } finally {
      setIsPreparingImage(false);
    }
  };

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
        <div className="col-span-2 space-y-3">
          <Input
            label="Image URL"
            type="url"
            placeholder="https://example.com/product.jpg"
            value={imageFromDevice ? '' : form.image_url}
            onChange={(e) => {
              setImageError(null);
              setForm({ ...form, image_url: e.target.value });
            }}
          />
          <div className="flex flex-wrap items-center gap-3">
            <label
              className={`btn-secondary inline-flex cursor-pointer items-center px-4 py-2 text-sm ${
                isPreparingImage ? 'pointer-events-none opacity-60' : ''
              }`}
            >
              <input
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={handleImageFile}
                disabled={isPreparingImage}
              />
              {isPreparingImage ? 'Preparing image...' : 'Choose from device'}
            </label>
            {form.image_url && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setImageError(null);
                  setForm({ ...form, image_url: '' });
                }}
              >
                Remove image
              </Button>
            )}
          </div>
          <p className="text-xs text-surface-400">
            Choose an image from your device; it is resized before saving.
          </p>
          {imageError && (
            <p role="alert" className="text-xs text-error">
              {imageError}
            </p>
          )}
        </div>
        {form.image_url.trim() && (
          <div className="col-span-2 flex items-center gap-3 rounded-md border border-surface-100 p-3">
            <img
              src={form.image_url}
              alt="Product preview"
              className="h-16 w-16 rounded object-cover"
            />
            <p className="text-xs text-surface-400">
              {imageFromDevice ? 'Selected from device' : 'Image preview'}
            </p>
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

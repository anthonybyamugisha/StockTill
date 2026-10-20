import { useEffect, useState } from 'react';
import { CartDiscountType, CartItem } from '../api/pos';
import { parseQuantityInput } from '../lib/quantity';
import { discountAmount } from '../lib/discounts';

interface QuantityInputProps {
  value: number;
  name: string;
  onChange: (quantity: number) => void;
}

function QuantityInput({ value, name, onChange }: QuantityInputProps) {
  const [draft, setDraft] = useState(String(value));

  useEffect(() => {
    setDraft(String(value));
  }, [value]);

  return (
    <input
      type="number"
      inputMode="numeric"
      min={1}
      step={1}
      value={draft}
      onChange={(event) => {
        const raw = event.target.value;
        setDraft(raw);
        const parsed = parseQuantityInput(raw);
        if (parsed !== null) onChange(parsed);
      }}
      onBlur={() => setDraft(String(value))}
      aria-label={`Quantity of ${name}`}
      className="w-16 rounded-md border border-surface-200 px-2 py-1 text-center text-sm focus:border-primary-400 focus:outline-none"
    />
  );
}

interface CartProps {
  items: CartItem[];
  onUpdateQuantity: (productId: string, quantity: number) => void;
  onUpdateDiscount: (productId: string, type: CartDiscountType, value: string) => void;
  onClearDiscount: (productId: string) => void;
  onRemove: (productId: string) => void;
}

interface DiscountEditorProps {
  item: CartItem;
  onApply: (type: CartDiscountType, value: string) => void;
  onClear: () => void;
  onClose: () => void;
}

function DiscountEditor({ item, onApply, onClear, onClose }: DiscountEditorProps) {
  const [type, setType] = useState<CartDiscountType>(item.discount_type ?? 'percentage');
  const [value, setValue] = useState(item.discount_value ?? '');

  return (
    <div className="mt-2 flex flex-wrap items-end gap-2 rounded-md bg-surface-50 p-2">
      <label className="text-xs text-surface-500">
        Type
        <select
          value={type}
          onChange={(event) => setType(event.target.value as CartDiscountType)}
          className="ml-1 rounded border border-surface-200 px-2 py-1 text-xs"
        >
          <option value="percentage">Percent</option>
          <option value="fixed">Fixed UGX</option>
        </select>
      </label>
      <label className="text-xs text-surface-500">
        {type === 'percentage' ? 'Percent off' : 'Amount off'}
        <input
          type="number"
          min={0}
          step="0.01"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="ml-1 w-24 rounded border border-surface-200 px-2 py-1 text-xs"
        />
      </label>
      <button
        type="button"
        onClick={() => onApply(type, value)}
        disabled={!value || Number(value) <= 0}
        className="rounded bg-primary-600 px-2 py-1 text-xs font-medium text-white disabled:opacity-50"
      >
        Apply
      </button>
      <button type="button" onClick={onClose} className="px-2 py-1 text-xs text-surface-500">
        Cancel
      </button>
      {item.discount_type && (
        <button type="button" onClick={onClear} className="px-2 py-1 text-xs text-red-600">
          Remove discount
        </button>
      )}
    </div>
  );
}

export function Cart({
  items,
  onUpdateQuantity,
  onUpdateDiscount,
  onClearDiscount,
  onRemove,
}: CartProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-2">
      {items.length === 0 && <p className="text-surface-400">Cart is empty</p>}
      {items.map((item) => {
        const discount = discountAmount(
          item.unit_price,
          item.quantity,
          item.discount_type,
          item.discount_value,
        );
        return (
          <div key={item.product_id} className="border-b border-surface-100 py-2">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-surface-700">{item.name}</p>
                <p className="text-sm text-surface-400">UGX {item.unit_price}</p>
                {discount > 0 && (
                  <p className="text-xs text-green-700">
                    Discount -UGX {discount.toFixed(2)}
                    {item.discount_type === 'percentage' && item.discount_value
                      ? ` (${item.discount_value}%)`
                      : ''}
                  </p>
                )}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button
                  type="button"
                  onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
                  aria-label={`Decrease quantity of ${item.name}`}
                  className="h-8 w-8 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200"
                >
                  -
                </button>
                <QuantityInput
                  value={item.quantity}
                  name={item.name}
                  onChange={(quantity) => onUpdateQuantity(item.product_id, quantity)}
                />
                <button
                  type="button"
                  onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
                  aria-label={`Increase quantity of ${item.name}`}
                  className="h-8 w-8 rounded-md bg-surface-100 text-surface-600 hover:bg-surface-200"
                >
                  +
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(item.product_id)}
                  className="ml-1 text-sm text-red-600"
                >
                  Remove
                </button>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setEditingId(editingId === item.product_id ? null : item.product_id)}
              className="mt-1 text-xs font-medium text-primary-600 hover:text-primary-700"
            >
              {item.discount_type ? 'Edit discount' : 'Add discount'}
            </button>
            {editingId === item.product_id && (
              <DiscountEditor
                item={item}
                onApply={(type, value) => {
                  onUpdateDiscount(item.product_id, type, value);
                  setEditingId(null);
                }}
                onClear={() => {
                  onClearDiscount(item.product_id);
                  setEditingId(null);
                }}
                onClose={() => setEditingId(null)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

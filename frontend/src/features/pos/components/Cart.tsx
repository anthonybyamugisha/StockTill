import { useEffect, useState } from 'react';
import { CartItem } from '../api/pos';
import { parseQuantityInput } from '../lib/quantity';

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
  onRemove: (productId: string) => void;
}

export function Cart({ items, onUpdateQuantity, onRemove }: CartProps) {
  return (
    <div className="flex flex-col gap-2">
      {items.length === 0 && <p className="text-surface-400">Cart is empty</p>}
      {items.map((item) => (
        <div
          key={item.product_id}
          className="flex items-center justify-between gap-3 border-b border-surface-100 py-2"
        >
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium text-surface-700">{item.name}</p>
            <p className="text-sm text-surface-400">UGX {item.unit_price}</p>
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
      ))}
    </div>
  );
}

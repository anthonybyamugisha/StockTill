import { CartItem } from '../api/pos';

interface CartProps {
  items: CartItem[];
  onUpdateQuantity: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
}

export function Cart({ items, onUpdateQuantity, onRemove }: CartProps) {
  return (
    <div className="flex flex-col gap-2">
      {items.length === 0 && <p className="text-gray-500">Cart is empty</p>}
      {items.map((item) => (
        <div key={item.product_id} className="flex items-center justify-between border-b py-2">
          <div>
            <p className="font-medium">{item.name}</p>
            <p className="text-sm text-gray-500">UGX {item.unit_price}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
              className="rounded bg-gray-200 px-2 py-1"
            >
              -
            </button>
            <span>{item.quantity}</span>
            <button
              onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
              className="rounded bg-gray-200 px-2 py-1"
            >
              +
            </button>
            <button
              onClick={() => onRemove(item.product_id)}
              className="ml-2 text-red-600"
            >
              Remove
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

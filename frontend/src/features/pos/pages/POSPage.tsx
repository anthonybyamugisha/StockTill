import { useCart } from '../hooks/useCart';
import { Cart } from '../components/Cart';
import { ProductSearch } from '../components/ProductSearch';

export function POSPage() {
  const { items, addItem, removeItem, updateQuantity, clearCart, subtotal } = useCart();

  return (
    <div className="grid grid-cols-2 gap-6 p-6">
      <div>
        <h2 className="mb-4 text-lg font-semibold">Products</h2>
        <ProductSearch
          onAddToCart={(p) =>
            addItem({
              product_id: p.product_id,
              name: p.name,
              quantity: 1,
              unit_price: p.unit_price,
              unit_cost: p.unit_cost,
            })
          }
        />
      </div>
      <div>
        <h2 className="mb-4 text-lg font-semibold">Cart</h2>
        <Cart items={items} onUpdateQuantity={updateQuantity} onRemove={removeItem} />
        <div className="mt-4 border-t pt-4">
          <p className="text-lg font-semibold">Subtotal: UGX {subtotal.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { useCart } from '../hooks/useCart';
import { Cart } from '../components/Cart';
import { ProductSearch } from '../components/ProductSearch';
import { PaymentModal } from '../components/PaymentModal';
import { Card } from '../../../shared/ui/Card';

export function POSPage() {
  const { items, addItem, removeItem, updateQuantity, clearCart, subtotal } = useCart();
  const [showPayment, setShowPayment] = useState(false);

  return (
    <div className="grid grid-cols-3 gap-6">
      <div className="col-span-2 space-y-4">
        <Card>
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
        </Card>
      </div>

      <div className="space-y-4">
        <Card title="Current Sale" subtitle={`${items.length} item(s)`}>
          <Cart items={items} onUpdateQuantity={updateQuantity} onRemove={removeItem} />
          <div className="mt-4 border-t border-surface-100 pt-4">
            <div className="flex justify-between text-lg font-semibold text-surface-600">
              <span>Subtotal</span>
              <span>UGX {subtotal.toFixed(2)}</span>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={clearCart} disabled={items.length === 0} className="btn-secondary flex-1">
              Clear
            </button>
            <button onClick={() => setShowPayment(true)} disabled={items.length === 0} className="btn-primary flex-1">
              Charge UGX {subtotal.toFixed(2)}
            </button>
          </div>
        </Card>
      </div>

      {showPayment && (
        <PaymentModal
          isOpen={showPayment}
          onClose={() => setShowPayment(false)}
          items={items}
          total={subtotal}
          onComplete={() => {
            clearCart();
            setShowPayment(false);
          }}
        />
      )}
    </div>
  );
}

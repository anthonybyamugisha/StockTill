import { useCallback, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useCart } from '../hooks/useCart';
import { Cart } from '../components/Cart';
import { ProductGrid } from '../components/ProductGrid';
import { PaymentModal } from '../components/PaymentModal';
import { BarcodeCameraModal } from '../components/BarcodeCameraModal';
import { Card } from '../../../shared/ui/Card';
import { useBarcodeScanner } from '../hooks/useBarcodeScanner';
import { lookupProductByBarcode, ProductLookup } from '../api/pos';
import { useAuth } from '../../auth/hooks/useAuth';
import { getSettings } from '../../settings/api/settings';
import { discountPercent } from '../lib/discounts';

interface ScanFeedback {
  type: 'success' | 'error';
  message: string;
}

export function POSPage() {
  const {
    items,
    addItem,
    removeItem,
    updateQuantity,
    updateDiscount,
    clearDiscount,
    clearCart,
    subtotal,
    discountTotal,
    total,
  } = useCart();
  const { user } = useAuth();
  const { data: settings } = useQuery({ queryKey: ['settings'], queryFn: getSettings });
  const [showPayment, setShowPayment] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [scanFeedback, setScanFeedback] = useState<ScanFeedback | null>(null);

  const cashierLimit =
    user?.role === 'cashier' && settings
      ? parseFloat(settings.cashier_discount_limit || '0')
      : null;
  const currentDiscountPercent = discountPercent(subtotal, discountTotal);
  const discountLimitExceeded =
    cashierLimit !== null && currentDiscountPercent > cashierLimit + 0.001;

  const handleScan = useCallback(
    async (barcode: string) => {
      try {
        const product = await lookupProductByBarcode(barcode);
        addItem({
          product_id: product.id,
          name: product.name,
          quantity: 1,
          unit_price: product.selling_price,
          unit_cost: product.buying_cost,
        });
        setScanFeedback({ type: 'success', message: `Added ${product.name}` });
      } catch {
        setScanFeedback({ type: 'error', message: `No product found for barcode ${barcode}` });
      }
    },
    [addItem],
  );

  useBarcodeScanner({ onScan: handleScan });

  const addProduct = useCallback(
    (product: ProductLookup) => {
      addItem({
        product_id: product.id,
        name: product.name,
        quantity: 1,
        unit_price: product.selling_price,
        unit_cost: product.buying_cost,
      });
    },
    [addItem],
  );

  useEffect(() => {
    if (!scanFeedback) return;
    const id = setTimeout(() => setScanFeedback(null), 3000);
    return () => clearTimeout(id);
  }, [scanFeedback]);

  return (
    <div className="grid grid-cols-3 gap-6">
      <div className="col-span-2 space-y-4">
        <Card>
          {scanFeedback && (
            <div
              className={`mb-3 rounded px-3 py-2 text-sm ${
                scanFeedback.type === 'success'
                  ? 'bg-green-50 text-green-700'
                  : 'bg-red-50 text-red-700'
              }`}
              role="status"
            >
              {scanFeedback.message}
            </div>
          )}
          <ProductGrid onSelect={addProduct} onScan={handleScan} />
          <p className="mt-3 text-xs text-surface-400">
            Tap a product to add it, or scan a barcode with a USB/Bluetooth scanner or the camera.
          </p>
          <button
            type="button"
            onClick={() => setShowCamera(true)}
            className="btn-secondary mt-3 w-full"
          >
            Scan with camera
          </button>
        </Card>
      </div>

      <div className="space-y-4">
        <Card
          title="Current Sale"
          subtitle={
            items.length === 0
              ? '0 item(s)'
              : `${items.length} item(s) · ${items.reduce((sum, item) => sum + item.quantity, 0)} unit(s)`
          }
        >
          <Cart
            items={items}
            onUpdateQuantity={updateQuantity}
            onUpdateDiscount={updateDiscount}
            onClearDiscount={clearDiscount}
            onRemove={removeItem}
          />
          <div className="mt-4 space-y-1 border-t border-surface-100 pt-4">
            <div className="flex justify-between text-sm text-surface-500">
              <span>Subtotal</span>
              <span>UGX {subtotal.toFixed(2)}</span>
            </div>
            {discountTotal > 0 && (
              <div className="flex justify-between text-sm text-green-700">
                <span>Discount</span>
                <span>-UGX {discountTotal.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-lg font-semibold text-surface-600">
              <span>Total</span>
              <span>UGX {total.toFixed(2)}</span>
            </div>
          </div>
          {discountLimitExceeded && (
            <p className="mt-2 rounded bg-red-50 px-3 py-2 text-xs text-error">
              Cashiers can discount up to {cashierLimit?.toFixed(2)}% of a sale. This sale is at{' '}
              {currentDiscountPercent.toFixed(2)}%.
            </p>
          )}
          <div className="mt-4 flex gap-2">
            <button onClick={clearCart} disabled={items.length === 0} className="btn-secondary flex-1">
              Clear
            </button>
            <button
              onClick={() => setShowPayment(true)}
              disabled={items.length === 0 || discountLimitExceeded}
              className="btn-primary flex-1"
            >
              Charge UGX {total.toFixed(2)}
            </button>
          </div>
        </Card>
      </div>

      {showPayment && (
        <PaymentModal
          isOpen={showPayment}
          onClose={() => setShowPayment(false)}
          items={items}
          total={total}
          onComplete={() => {
            clearCart();
            setShowPayment(false);
          }}
        />
      )}

      <BarcodeCameraModal
        isOpen={showCamera}
        onClose={() => setShowCamera(false)}
        onDetected={handleScan}
      />
    </div>
  );
}

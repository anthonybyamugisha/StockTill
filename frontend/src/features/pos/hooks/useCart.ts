import { useState, useCallback } from 'react';
import { CartItem, CartDiscountType } from '../api/pos';
import { discountAmount, lineGross, roundMoney } from '../lib/discounts';

export function useCart() {
  const [items, setItems] = useState<CartItem[]>([]);

  const addItem = useCallback((item: CartItem) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === item.product_id);
      if (existing) {
        return prev.map((i) =>
          i.product_id === item.product_id ? { ...i, quantity: i.quantity + 1 } : i,
        );
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  }, []);

  const removeItem = useCallback((productId: string) => {
    setItems((prev) => prev.filter((i) => i.product_id !== productId));
  }, []);

  const updateQuantity = useCallback((productId: string, quantity: number) => {
    setItems((prev) =>
      quantity <= 0
        ? prev.filter((i) => i.product_id !== productId)
        : prev.map((i) => (i.product_id === productId ? { ...i, quantity } : i)),
    );
  }, []);

  const updateDiscount = useCallback(
    (productId: string, type: CartDiscountType, value: string) => {
      setItems((prev) =>
        prev.map((item) =>
          item.product_id === productId
            ? { ...item, discount_type: type, discount_value: value }
            : item,
        ),
      );
    },
    [],
  );

  const clearDiscount = useCallback((productId: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.product_id === productId
          ? { ...item, discount_type: null, discount_value: null }
          : item,
      ),
    );
  }, []);

  const clearCart = useCallback(() => setItems([]), []);

  const subtotal = roundMoney(
    items.reduce((sum, item) => sum + lineGross(item.unit_price, item.quantity), 0),
  );
  const discountTotal = roundMoney(
    items.reduce(
      (sum, item) =>
        sum +
        discountAmount(item.unit_price, item.quantity, item.discount_type, item.discount_value),
      0,
    ),
  );
  const total = roundMoney(subtotal - discountTotal);

  return {
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
  };
}

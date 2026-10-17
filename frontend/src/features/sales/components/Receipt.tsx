interface ReceiptProps {
  receiptNumber: string;
  cashierName: string;
  date: string;
  items: Array<{
    name: string;
    quantity: number;
    price: number;
    total: number;
  }>;
  subtotal: number;
  discount: number;
  total: number;
  payments: Array<{
    method: string;
    amount: number;
    tendered?: number;
    change?: number;
  }>;
}

export function Receipt({ receiptNumber, cashierName, date, items, subtotal, discount, total, payments }: ReceiptProps) {
  return (
    <div className="mx-auto max-w-xs bg-white p-4 font-mono text-xs text-black">
      <div className="mb-2 text-center">
        <p className="text-sm font-bold">StockTill Shop</p>
        <p>Receipt: {receiptNumber}</p>
        <p>Cashier: {cashierName}</p>
        <p>{date}</p>
      </div>
      <div className="my-2 border-t border-dashed border-gray-300" />
      <div className="space-y-1">
        {items.map((item, i) => (
          <div key={i} className="flex justify-between">
            <span>{item.name}</span>
            <span>{item.quantity} x {item.price}</span>
          </div>
        ))}
      </div>
      <div className="my-2 border-t border-dashed border-gray-300" />
      <div className="space-y-1">
        <div className="flex justify-between"><span>Subtotal:</span><span>UGX {subtotal.toFixed(2)}</span></div>
        {discount > 0 && <div className="flex justify-between"><span>Discount:</span><span>-UGX {discount.toFixed(2)}</span></div>}
        <div className="flex justify-between font-bold"><span>TOTAL:</span><span>UGX {total.toFixed(2)}</span></div>
      </div>
      <div className="my-2 border-t border-dashed border-gray-300" />
      <div className="space-y-1">
        {payments.map((p, i) => (
          <div key={i} className="flex justify-between">
            <span>{p.method}:</span>
            <span>UGX {p.amount.toFixed(2)}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 text-center">
        <p>Thank you for shopping with us!</p>
      </div>
    </div>
  );
}

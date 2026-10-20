import { formatDateTime } from '../utils/date';
import {
  lineTotal,
  methodLabel,
  money,
  providerLabel,
  ReceiptBusiness,
  ReceiptSale,
} from '../utils/receipt';

interface ReceiptProps {
  sale: ReceiptSale;
  business?: ReceiptBusiness;
  cashierName?: string;
}

export function Receipt({ sale, business = {}, cashierName }: ReceiptProps) {
  const currency = business.currency || 'UGX';
  const totalDiscount = parseFloat(sale.total_discount || '0');

  return (
    <div
      id="receipt-print-area"
      className="mx-auto w-full max-w-xs bg-white p-4 font-mono text-xs text-black"
    >
      <div className="text-center">
        <p className="text-sm font-bold">{business.business_name || 'StockTill'}</p>
        {business.receipt_header && <p className="whitespace-pre-line">{business.receipt_header}</p>}
        {business.address && <p className="whitespace-pre-line">{business.address}</p>}
        {business.phone && <p>{business.phone}</p>}
      </div>

      <div className="my-2 border-t border-dashed border-gray-400" />

      <div className="space-y-0.5">
        <div className="flex justify-between">
          <span>Receipt</span>
          <span className="font-semibold">{sale.receipt_number}</span>
        </div>
        <div className="flex justify-between">
          <span>Date</span>
          <span>{formatDateTime(sale.created_at)}</span>
        </div>
        {cashierName && (
          <div className="flex justify-between">
            <span>Cashier</span>
            <span>{cashierName}</span>
          </div>
        )}
        {sale.status && sale.status !== 'completed' && (
          <div className="flex justify-between uppercase">
            <span>Status</span>
            <span>{sale.status.replace(/_/g, ' ')}</span>
          </div>
        )}
      </div>

      <div className="my-2 border-t border-dashed border-gray-400" />

      <div className="space-y-1.5">
        {sale.lines.map((line, index) => (
          <div key={index}>
            <p className="font-medium">{line.product_name}</p>
            <div className="flex justify-between">
              <span>
                {line.quantity} x {money(line.unit_price, currency)}
              </span>
              <span>{money(lineTotal(line), currency)}</span>
            </div>
            {line.discount_amount && parseFloat(line.discount_amount) > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>Discount</span>
                <span>-{money(line.discount_amount, currency)}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="my-2 border-t border-dashed border-gray-400" />

      <div className="space-y-0.5">
        <div className="flex justify-between">
          <span>Subtotal</span>
          <span>{money(sale.subtotal, currency)}</span>
        </div>
        {totalDiscount > 0 && (
          <div className="flex justify-between">
            <span>Discount</span>
            <span>-{money(totalDiscount, currency)}</span>
          </div>
        )}
        <div className="flex justify-between text-sm font-bold">
          <span>TOTAL</span>
          <span>{money(sale.total, currency)}</span>
        </div>
      </div>

      <div className="my-2 border-t border-dashed border-gray-400" />

      <div className="space-y-0.5">
        {sale.payments.map((payment, index) => (
          <div key={index}>
            <div className="flex justify-between">
              <span>{methodLabel(payment.method)}</span>
              <span>{money(payment.amount, currency)}</span>
            </div>
            {payment.provider && (
              <div className="flex justify-between">
                <span>Provider</span>
                <span>{providerLabel(payment.provider)}</span>
              </div>
            )}
            {payment.reference && (
              <div className="flex justify-between">
                <span>Reference</span>
                <span>{payment.reference}</span>
              </div>
            )}
            {payment.tendered && parseFloat(payment.tendered) > 0 && (
              <div className="flex justify-between">
                <span>Tendered</span>
                <span>{money(payment.tendered, currency)}</span>
              </div>
            )}
            {payment.change && parseFloat(payment.change) > 0 && (
              <div className="flex justify-between">
                <span>Change</span>
                <span>{money(payment.change, currency)}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="my-2 border-t border-dashed border-gray-400" />

      <p className="text-center whitespace-pre-line">
        {business.receipt_footer || 'Thank you for shopping with us!'}
      </p>
    </div>
  );
}

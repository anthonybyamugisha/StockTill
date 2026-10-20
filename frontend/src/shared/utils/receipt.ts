import { formatDateTime } from './date';

export interface ReceiptLine {
  product_name: string;
  quantity: number;
  unit_price: string;
  discount_amount?: string;
  total?: string;
}

export interface ReceiptPayment {
  method: string;
  amount: string;
  tendered?: string | null;
  change?: string | null;
  reference?: string | null;
  provider?: string | null;
}

export interface ReceiptSale {
  receipt_number: string;
  created_at: string;
  status?: string;
  lines: ReceiptLine[];
  payments: ReceiptPayment[];
  subtotal: string;
  total_discount?: string;
  total: string;
  amount_paid?: string;
}

export interface ReceiptBusiness {
  business_name?: string;
  address?: string;
  phone?: string;
  email?: string;
  currency?: string;
  receipt_header?: string;
  receipt_footer?: string;
}

const METHOD_LABELS: Record<string, string> = {
  cash: 'Cash',
  card: 'Card',
  mobile_money: 'Mobile Money',
  bank_transfer: 'Bank Transfer',
};

const PROVIDER_LABELS: Record<string, string> = {
  mtn: 'MTN MoMo',
  airtel: 'Airtel Money',
  manual: 'Manual',
};

const WIDTH = 40;

export function round2(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

export function methodLabel(method: string): string {
  return (
    METHOD_LABELS[method] ??
    method
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

export function providerLabel(provider: string): string {
  return (
    PROVIDER_LABELS[provider.toLowerCase()] ??
    provider.replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

export function lineTotal(line: ReceiptLine): number {
  if (line.total !== undefined && line.total !== null) {
    return parseFloat(line.total);
  }
  const discount = line.discount_amount ? parseFloat(line.discount_amount) : 0;
  return round2(line.quantity * parseFloat(line.unit_price) - discount);
}

export function money(value: string | number, currency = 'UGX'): string {
  const amount = typeof value === 'string' ? parseFloat(value) : value;
  return `${currency} ${(Number.isFinite(amount) ? amount : 0).toFixed(2)}`;
}

function padLine(left: string, right: string): string {
  const space = Math.max(1, WIDTH - left.length - right.length);
  return left + ' '.repeat(space) + right;
}

function center(text: string): string {
  if (text.length >= WIDTH) return text;
  const left = Math.floor((WIDTH - text.length) / 2);
  return ' '.repeat(left) + text;
}

export function buildReceiptText(
  sale: ReceiptSale,
  business: ReceiptBusiness = {},
  cashierName = '',
): string {
  const currency = business.currency || 'UGX';
  const out: string[] = [];

  out.push(center(business.business_name || 'StockTill'));
  if (business.receipt_header) out.push(center(business.receipt_header));
  if (business.address) out.push(center(business.address));
  if (business.phone) out.push(center(business.phone));
  out.push('='.repeat(WIDTH));
  out.push(`Receipt: ${sale.receipt_number}`);
  out.push(`Date: ${formatDateTime(sale.created_at)}`);
  if (cashierName) out.push(`Cashier: ${cashierName}`);
  if (sale.status && sale.status !== 'completed') out.push(`Status: ${sale.status}`);
  out.push('-'.repeat(WIDTH));

  for (const line of sale.lines) {
    out.push(line.product_name);
    out.push(padLine(`  ${line.quantity} x ${money(line.unit_price, currency)}`, money(lineTotal(line), currency)));
    const discount = line.discount_amount ? parseFloat(line.discount_amount) : 0;
    if (discount > 0) out.push(padLine('  Discount', `-${money(discount, currency)}`));
  }

  out.push('-'.repeat(WIDTH));
  out.push(padLine('Subtotal', money(sale.subtotal, currency)));
  const totalDiscount = parseFloat(sale.total_discount || '0');
  if (totalDiscount > 0) out.push(padLine('Discount', `-${money(totalDiscount, currency)}`));
  out.push(padLine('TOTAL', money(sale.total, currency)));
  out.push('-'.repeat(WIDTH));

  for (const payment of sale.payments) {
    out.push(padLine(methodLabel(payment.method), money(payment.amount, currency)));
    if (payment.provider) out.push(padLine('  Provider', providerLabel(payment.provider)));
    if (payment.reference) out.push(padLine('  Reference', payment.reference));
    const tendered = payment.tendered ? parseFloat(payment.tendered) : 0;
    if (tendered > 0) out.push(padLine('  Tendered', money(tendered, currency)));
    const change = payment.change ? parseFloat(payment.change) : 0;
    if (change > 0) out.push(padLine('  Change', money(change, currency)));
  }

  out.push('='.repeat(WIDTH));
  out.push(center(business.receipt_footer || 'Thank you for shopping with us!'));
  return out.join('\n');
}

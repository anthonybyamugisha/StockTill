export type DiscountType = 'percentage' | 'fixed';

export function roundMoney(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

export function lineGross(unitPrice: string, quantity: number): number {
  return roundMoney(parseFloat(unitPrice) * quantity);
}

export function discountAmount(
  unitPrice: string,
  quantity: number,
  type: DiscountType | null | undefined,
  value: string | number | null | undefined,
): number {
  const gross = lineGross(unitPrice, quantity);
  const parsed = typeof value === 'number' ? value : parseFloat(value ?? '');
  if (!type || !Number.isFinite(parsed) || parsed <= 0 || gross <= 0) return 0;
  const amount = type === 'percentage' ? gross * (parsed / 100) : parsed;
  return roundMoney(Math.min(Math.max(amount, 0), gross));
}

export function lineTotal(
  unitPrice: string,
  quantity: number,
  type: DiscountType | null | undefined,
  value: string | number | null | undefined,
): number {
  return roundMoney(lineGross(unitPrice, quantity) - discountAmount(unitPrice, quantity, type, value));
}

export function discountPercent(subtotal: number, discountTotal: number): number {
  if (subtotal <= 0) return 0;
  return (discountTotal / subtotal) * 100;
}

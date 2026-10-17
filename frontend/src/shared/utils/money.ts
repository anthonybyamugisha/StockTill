export function formatMoney(amount: string | number, currency: string = 'UGX'): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return `${currency} ${num.toLocaleString('en-UG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function parseMoney(value: string): number {
  return parseFloat(value.replace(/[^0-9.-]/g, ''));
}

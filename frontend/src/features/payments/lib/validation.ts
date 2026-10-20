export function normalizePhone(raw: string, countryCode = '256'): string {
  let digits = raw.replace(/\D/g, '');
  if (digits.startsWith('00')) digits = digits.slice(2);
  if (digits.startsWith(countryCode)) return digits;
  if (digits.startsWith('0')) return `${countryCode}${digits.slice(1)}`;
  if (digits.length === 9) return `${countryCode}${digits}`;
  return digits;
}

export function validatePhone(raw: string): string | null {
  const normalized = normalizePhone(raw);
  if (normalized.length < 9 || normalized.length > 15) {
    return 'Enter a valid phone number, for example 0772 123 456.';
  }
  return null;
}

export function validateTendered(tendered: string, total: number): string | null {
  if (!tendered.trim()) return null;
  const value = Number(tendered);
  if (!Number.isFinite(value)) return 'Enter a valid amount.';
  if (value < total) return 'Tendered is less than the amount due.';
  return null;
}

export function calculateChange(tendered: string, total: number): number {
  if (!tendered.trim()) return 0;
  const value = Number(tendered);
  if (!Number.isFinite(value) || value <= total) return 0;
  return Math.round((value - total + Number.EPSILON) * 100) / 100;
}

export function validateReference(method: string, reference: string): string | null {
  if (method !== 'card' && method !== 'bank_transfer') return null;
  if (!reference.trim()) {
    return 'Add the reference from the card terminal or bank.';
  }
  return null;
}

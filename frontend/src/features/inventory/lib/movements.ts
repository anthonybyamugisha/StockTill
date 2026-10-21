const MOVEMENT_LABELS: Record<string, string> = {
  opening: 'Opening stock',
  purchase: 'Purchase',
  sale: 'Sale',
  refund_return: 'Refund return',
  adjustment_in: 'Adjustment in',
  adjustment_out: 'Adjustment out',
  write_off: 'Write off',
};

const STOCK_REDUCING = new Set(['sale', 'adjustment_out', 'write_off']);

export function movementLabel(movementType: string): string {
  return MOVEMENT_LABELS[movementType] ?? movementType;
}

export function movementQuantity(movementType: string, quantity: number): number {
  return STOCK_REDUCING.has(movementType) ? -Math.abs(quantity) : Math.abs(quantity);
}

export function formatMovementQuantity(movementType: string, quantity: number): string {
  const value = movementQuantity(movementType, quantity);
  return `${value > 0 ? '+' : ''}${value}`;
}

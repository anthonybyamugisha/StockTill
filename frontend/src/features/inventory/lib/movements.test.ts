import { describe, expect, it } from 'vitest';
import { formatMovementQuantity, movementLabel, movementQuantity } from './movements';

describe('inventory movement formatting', () => {
  it('labels known movement types', () => {
    expect(movementLabel('adjustment_in')).toBe('Adjustment in');
    expect(movementLabel('write_off')).toBe('Write off');
  });

  it('falls back to the raw movement type', () => {
    expect(movementLabel('custom')).toBe('custom');
  });

  it('makes stock-reducing movements negative', () => {
    expect(movementQuantity('sale', 3)).toBe(-3);
    expect(movementQuantity('adjustment_out', 2)).toBe(-2);
    expect(movementQuantity('write_off', 1)).toBe(-1);
  });

  it('keeps stock-adding movements positive', () => {
    expect(movementQuantity('adjustment_in', -4)).toBe(4);
    expect(movementQuantity('opening', 5)).toBe(5);
  });

  it('formats signed quantities', () => {
    expect(formatMovementQuantity('purchase', 10)).toBe('+10');
    expect(formatMovementQuantity('sale', 2)).toBe('-2');
  });
});

import { describe, expect, it } from 'vitest';
import { ProductLookup } from '../api/pos';
import { filterProducts } from './productFilter';

function product(overrides: Partial<ProductLookup>): ProductLookup {
  return {
    id: 'id',
    name: 'Product',
    sku: 'SKU',
    barcode: null,
    selling_price: '10.00',
    buying_cost: '5.00',
    category_id: null,
    minimum_stock_level: 0,
    image_url: null,
    ...overrides,
  };
}

const catalogue = [
  product({ id: '1', name: 'Sugar 1kg', sku: 'SUG-1', barcode: '111', category_id: 'a' }),
  product({ id: '2', name: 'Cooking Oil', sku: 'OIL-5', barcode: '222', category_id: 'b' }),
  product({ id: '3', name: 'Salt', sku: 'SLT-1', barcode: '333', category_id: 'a' }),
];

describe('filterProducts', () => {
  it('returns everything when there is no query or category', () => {
    expect(filterProducts(catalogue, '', null)).toHaveLength(3);
  });

  it('matches by name, case-insensitively', () => {
    expect(filterProducts(catalogue, 'sugar', null).map((p) => p.id)).toEqual(['1']);
  });

  it('matches by sku', () => {
    expect(filterProducts(catalogue, 'OIL', null).map((p) => p.id)).toEqual(['2']);
  });

  it('matches by barcode', () => {
    expect(filterProducts(catalogue, '333', null).map((p) => p.id)).toEqual(['3']);
  });

  it('filters by category', () => {
    expect(filterProducts(catalogue, '', 'a').map((p) => p.id)).toEqual(['1', '3']);
  });

  it('combines a category and a query', () => {
    expect(filterProducts(catalogue, 'salt', 'a').map((p) => p.id)).toEqual(['3']);
    expect(filterProducts(catalogue, 'salt', 'b')).toHaveLength(0);
  });
});

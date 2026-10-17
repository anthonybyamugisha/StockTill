export interface SearchableProduct {
  name: string;
  sku: string;
  barcode?: string | null;
}

export function matchesProductQuery(product: SearchableProduct, query: string): boolean {
  const term = query.trim().toLowerCase();
  if (!term) return true;
  return (
    product.name.toLowerCase().includes(term) ||
    product.sku.toLowerCase().includes(term) ||
    (product.barcode ?? '').toLowerCase().includes(term)
  );
}

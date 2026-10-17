import { ProductLookup } from '../api/pos';

export function filterProducts(
  products: ProductLookup[],
  query: string,
  categoryId: string | null,
): ProductLookup[] {
  const term = query.trim().toLowerCase();
  return products.filter((product) => {
    if (categoryId && product.category_id !== categoryId) return false;
    if (!term) return true;
    return (
      product.name.toLowerCase().includes(term) ||
      product.sku.toLowerCase().includes(term) ||
      (product.barcode ?? '').toLowerCase().includes(term)
    );
  });
}

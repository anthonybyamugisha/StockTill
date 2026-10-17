import { ProductLookup } from '../api/pos';
import { matchesProductQuery } from '../../../shared/utils/productSearch';

export function filterProducts(
  products: ProductLookup[],
  query: string,
  categoryId: string | null,
): ProductLookup[] {
  return products.filter((product) => {
    if (categoryId && product.category_id !== categoryId) return false;
    return matchesProductQuery(product, query);
  });
}

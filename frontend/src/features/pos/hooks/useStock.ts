import { useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listStockItems } from '../../inventory/api/inventory';

export function useStockByProduct() {
  const { data: stockItems = [] } = useQuery({
    queryKey: ['stockItems'],
    queryFn: listStockItems,
  });

  const stockById = useMemo(
    () => new Map(stockItems.map((item) => [item.product_id, item.available_quantity])),
    [stockItems],
  );

  const getAvailable = useCallback((productId: string) => stockById.get(productId) ?? 0, [stockById]);

  return { stockById, getAvailable };
}

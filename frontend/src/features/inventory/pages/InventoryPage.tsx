import { useQuery } from '@tanstack/react-query';
import { getLowStock, getOutOfStock } from '../api/inventory';

export function InventoryPage() {
  const { data: lowStock } = useQuery({ queryKey: ['lowStock'], queryFn: getLowStock });
  const { data: outOfStock } = useQuery({ queryKey: ['outOfStock'], queryFn: getOutOfStock });

  return (
    <div className="p-6">
      <h1 className="mb-4 text-2xl font-bold">Inventory</h1>
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="mb-2 text-lg font-semibold">Low Stock</h2>
          <ul className="space-y-1">
            {lowStock?.map((item) => (
              <li key={item.product_id} className="border-b py-1">
                Product {item.product_id}: {item.quantity_on_hand} units
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="mb-2 text-lg font-semibold">Out of Stock</h2>
          <ul className="space-y-1">
            {outOfStock?.map((item) => (
              <li key={item.product_id} className="border-b py-1">
                Product {item.product_id}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

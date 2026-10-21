import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getLowStock,
  getOutOfStock,
  getStockHistory,
  getValuation,
  listStockItems,
  adjustStock,
  StockItem,
} from '../api/inventory';
import { AdjustStockModal } from '../components/AdjustStockModal';
import {
  formatMovementQuantity,
  movementLabel,
} from '../lib/movements';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { listProducts, Product } from '../../catalog/api/catalog';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { formatMoney } from '../../../shared/utils/money';
import { formatDateTime } from '../../../shared/utils/date';

interface InventoryRow {
  product: Product;
  quantity: number;
  reserved: number;
  available: number;
}

export function InventoryPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'overview' | 'history'>('overview');
  const [search, setSearch] = useState('');
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [adjustProductId, setAdjustProductId] = useState('');
  const [historyProductId, setHistoryProductId] = useState('');

  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => listProducts(),
  });
  const { data: stockItems = [] } = useQuery({
    queryKey: ['stockItems'],
    queryFn: listStockItems,
  });
  const { data: lowStock } = useQuery({ queryKey: ['lowStock'], queryFn: getLowStock });
  const { data: outOfStock } = useQuery({ queryKey: ['outOfStock'], queryFn: getOutOfStock });
  const { data: valuation } = useQuery({ queryKey: ['valuation'], queryFn: getValuation });
  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['stockHistory', historyProductId],
    queryFn: () => getStockHistory(historyProductId),
    enabled: Boolean(historyProductId),
  });

  const stockByProduct = useMemo(
    () => new Map<string, StockItem>(stockItems.map((item) => [item.product_id, item])),
    [stockItems],
  );

  const rows = useMemo<InventoryRow[]>(
    () =>
      products.map((product) => {
        const stock = stockByProduct.get(product.id);
        const quantity = stock?.quantity_on_hand ?? 0;
        const reserved = stock?.reserved_quantity ?? 0;
        return {
          product,
          quantity,
          reserved,
          available: stock?.available_quantity ?? quantity,
        };
      }),
    [products, stockByProduct],
  );

  const visibleRows = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return rows;
    return rows.filter(
      (row) =>
        row.product.name.toLowerCase().includes(term) ||
        row.product.sku.toLowerCase().includes(term),
    );
  }, [rows, search]);

  const adjustMutation = useMutation({
    mutationFn: adjustStock,
    onSuccess: (_movement, variables) => {
      queryClient.invalidateQueries({ queryKey: ['lowStock'] });
      queryClient.invalidateQueries({ queryKey: ['outOfStock'] });
      queryClient.invalidateQueries({ queryKey: ['stockItems'] });
      queryClient.invalidateQueries({ queryKey: ['valuation'] });
      queryClient.invalidateQueries({ queryKey: ['stockHistory', variables.product_id] });
      setShowAdjustModal(false);
      const name = products.find((product) => product.id === variables.product_id)?.name;
      const removed =
        variables.movement_type === 'adjustment_out' ||
        variables.movement_type === 'write_off';
      toast.success(
        `Stock ${removed ? 'reduced' : 'increased'} by ${variables.quantity} for "${
          name ?? 'product'
        }"`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not adjust stock')),
  });

  const openAdjustment = (productId = '') => {
    setAdjustProductId(productId);
    setShowAdjustModal(true);
  };

  const openHistory = (productId: string) => {
    setHistoryProductId(productId);
    setTab('history');
  };

  const overviewColumns = [
    {
      key: 'product',
      header: 'Product',
      render: (row: InventoryRow) => (
        <div>
          <p className="font-medium text-surface-700">{row.product.name}</p>
          <p className="text-xs text-surface-400">SKU: {row.product.sku}</p>
        </div>
      ),
    },
    {
      key: 'quantity',
      header: 'On hand',
      render: (row: InventoryRow) => row.quantity,
    },
    {
      key: 'reserved',
      header: 'Reserved',
      render: (row: InventoryRow) => row.reserved,
    },
    {
      key: 'available',
      header: 'Available',
      render: (row: InventoryRow) => row.available,
    },
    {
      key: 'value',
      header: 'Stock value',
      render: (row: InventoryRow) =>
        formatMoney(Number(row.product.buying_cost) * row.quantity),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: InventoryRow) => {
        if (row.quantity === 0) return <Badge variant="error">Out of stock</Badge>;
        if (row.quantity <= row.product.minimum_stock_level) {
          return <Badge variant="warning">Low stock</Badge>;
        }
        return <Badge variant="success">In stock</Badge>;
      },
    },
    {
      key: 'actions',
      header: '',
      render: (row: InventoryRow) => (
        <div className="flex gap-1">
          <button onClick={() => openAdjustment(row.product.id)} className="btn-ghost btn-sm">
            Adjust
          </button>
          <button onClick={() => openHistory(row.product.id)} className="btn-ghost btn-sm">
            History
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-surface-400">Stock Value at Cost</p>
          <p className="mt-1 text-2xl font-semibold text-surface-700">
            {formatMoney(valuation?.total ?? '0')}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Low Stock Alerts</p>
          <p className="mt-1 text-2xl font-semibold text-warning">{lowStock?.length ?? 0}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Out of Stock</p>
          <p className="mt-1 text-2xl font-semibold text-error">{outOfStock?.length ?? 0}</p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="inline-flex rounded-md border border-surface-200 bg-white p-1">
          <button
            onClick={() => setTab('overview')}
            className={`rounded px-4 py-1.5 text-sm font-medium ${
              tab === 'overview'
                ? 'bg-primary-500 text-white'
                : 'text-surface-500 hover:bg-surface-50'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setTab('history')}
            className={`rounded px-4 py-1.5 text-sm font-medium ${
              tab === 'history'
                ? 'bg-primary-500 text-white'
                : 'text-surface-500 hover:bg-surface-50'
            }`}
          >
            History
          </button>
        </div>
        <Button onClick={() => openAdjustment()}>Adjust Stock</Button>
      </div>

      {tab === 'overview' ? (
        <Card>
          <div className="mb-4">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by product or SKU..."
              className="input w-80"
            />
          </div>
          <Table
            columns={overviewColumns}
            data={visibleRows}
            keyExtractor={(row) => row.product.id}
            emptyMessage={search.trim() ? 'No products match your search' : 'No products found'}
          />
        </Card>
      ) : (
        <Card>
          <div className="mb-4 flex items-end gap-3">
            <div className="w-80">
              <label className="label">Product</label>
              <select
                className="input"
                value={historyProductId}
                onChange={(e) => setHistoryProductId(e.target.value)}
              >
                <option value="">Select a product</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
                  </option>
                ))}
              </select>
            </div>
            {historyProductId && (
              <Button variant="secondary" onClick={() => openAdjustment(historyProductId)}>
                Adjust this product
              </Button>
            )}
          </div>

          {!historyProductId ? (
            <p className="py-8 text-center text-sm text-surface-400">
              Select a product to see its stock movements.
            </p>
          ) : historyLoading ? (
            <p className="py-8 text-center text-surface-400">Loading history...</p>
          ) : (
            <Table
              columns={[
                {
                  key: 'date',
                  header: 'When',
                  render: (movement) => formatDateTime(movement.timestamp),
                },
                {
                  key: 'type',
                  header: 'Movement',
                  render: (movement) => movementLabel(movement.movement_type),
                },
                {
                  key: 'quantity',
                  header: 'Quantity',
                  render: (movement) => (
                    <span
                      className={
                        formatMovementQuantity(movement.movement_type, movement.quantity).startsWith(
                          '-',
                        )
                          ? 'font-medium text-error'
                          : 'font-medium text-success'
                      }
                    >
                      {formatMovementQuantity(movement.movement_type, movement.quantity)}
                    </span>
                  ),
                },
                {
                  key: 'reason',
                  header: 'Reason',
                  render: (movement) => movement.reason,
                },
                {
                  key: 'reference',
                  header: 'Reference',
                  render: (movement) => movement.reference || '—',
                },
              ]}
              data={history}
              keyExtractor={(movement) => movement.id}
              emptyMessage="No stock movements recorded for this product"
            />
          )}
        </Card>
      )}

      {showAdjustModal && (
        <AdjustStockModal
          products={products}
          initialProductId={adjustProductId}
          lockProduct={Boolean(adjustProductId)}
          onClose={() => setShowAdjustModal(false)}
          onSubmit={(data) => adjustMutation.mutate(data)}
          isLoading={adjustMutation.isPending}
        />
      )}
    </div>
  );
}

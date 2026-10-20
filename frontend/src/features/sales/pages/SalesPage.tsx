import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listSales, refundSale, voidSale } from '../api/sales';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { Modal } from '../../../shared/ui/Modal';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
import { formatDateTime } from '../../../shared/utils/date';
import { Receipt } from '../../../shared/ui/Receipt';
import { getSettings } from '../../settings/api/settings';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { useAuth } from '../../auth/hooks/useAuth';
import { listCashiers } from '../../users/api/users';
import { PAYMENT_METHOD_OPTIONS } from '../../payments/lib/paymentMethods';

export function SalesPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canViewAllCashiers = user?.role !== 'cashier';
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [cashierFilter, setCashierFilter] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [receiptSearch, setReceiptSearch] = useState('');
  const [showDetail, setShowDetail] = useState<any>(null);

  const { data: cashiers } = useQuery({
    queryKey: ['cashiers'],
    queryFn: listCashiers,
    enabled: canViewAllCashiers,
  });

  const { data: sales, isLoading, isError, error } = useQuery({
    queryKey: ['sales', dateFrom, dateTo, statusFilter, cashierFilter, paymentFilter, receiptSearch],
    queryFn: () => listSales({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      status: statusFilter || undefined,
      cashier_id: canViewAllCashiers ? cashierFilter || undefined : undefined,
      payment_method: paymentFilter || undefined,
      receipt_number: receiptSearch || undefined,
    }),
  });

  const refundMutation = useMutation({
    mutationFn: refundSale,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales'] });
      setShowDetail(null);
      toast.success(`Refund recorded for ${showDetail?.receipt_number ?? 'the sale'}`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not record the refund')),
  });

  const voidMutation = useMutation({
    mutationFn: voidSale,
    onSuccess: (sale) => {
      queryClient.invalidateQueries({ queryKey: ['sales'] });
      setShowDetail(null);
      toast.success(`Sale ${sale.receipt_number} voided — stock restored`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not void the sale')),
  });

  const statusColors: Record<string, 'success' | 'warning' | 'error' | 'neutral'> = {
    completed: 'success',
    partially_refunded: 'warning',
    refunded: 'error',
    voided: 'neutral',
  };

  const statusOptions = [
    { value: '', label: 'All statuses' },
    { value: 'completed', label: 'Completed' },
    { value: 'partially_refunded', label: 'Partially refunded' },
    { value: 'refunded', label: 'Refunded' },
    { value: 'voided', label: 'Voided' },
  ];

  const paymentOptions = [
    { value: '', label: 'All payment methods' },
    ...PAYMENT_METHOD_OPTIONS.map((option) => ({ value: option.value, label: option.label })),
  ];

  const cashierOptions = [
    { value: '', label: 'All cashiers' },
    ...(cashiers ?? []).map((cashier) => ({
      value: cashier.id,
      label: `${cashier.first_name} ${cashier.last_name}`.trim(),
    })),
  ];

  const hasFilters =
    dateFrom || dateTo || statusFilter || cashierFilter || paymentFilter || receiptSearch;

  return (
    <div className="space-y-4">
      <Card>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
          <Input label="From Date" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <Input label="To Date" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          <Select
            label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            options={statusOptions}
          />
          <Select
            label="Payment"
            value={paymentFilter}
            onChange={(e) => setPaymentFilter(e.target.value)}
            options={paymentOptions}
          />
          {canViewAllCashiers && (
            <Select
              label="Cashier"
              value={cashierFilter}
              onChange={(e) => setCashierFilter(e.target.value)}
              options={cashierOptions}
            />
          )}
          <Input
            label="Receipt"
            value={receiptSearch}
            onChange={(e) => setReceiptSearch(e.target.value)}
            placeholder="e.g. 000012"
          />
        </div>
        <div className="mt-4 flex items-center justify-between gap-3">
          <p className="text-xs text-surface-400">
            {user?.role === 'cashier'
              ? 'Showing sales completed by you.'
              : 'Showing sales from all cashiers.'}
          </p>
          <Button
            variant="secondary"
            onClick={() => {
              setDateFrom('');
              setDateTo('');
              setStatusFilter('');
              setCashierFilter('');
              setPaymentFilter('');
              setReceiptSearch('');
            }}
          >
            Clear Filters
          </Button>
        </div>
      </Card>

      <Card>
        {isLoading ? (
          <p className="py-8 text-center text-surface-400">Loading sales...</p>
        ) : isError ? (
          <p className="py-8 text-center text-error">
            {getApiErrorMessage(error, 'Could not load sales')}
          </p>
        ) : (
          <Table
            columns={[
              { key: 'receipt', header: 'Receipt', render: (s: any) => <span className="font-medium">{s.receipt_number}</span> },
              { key: 'date', header: 'Date', render: (s: any) => formatDateTime(s.created_at) },
              { key: 'total', header: 'Total', render: (s: any) => `UGX ${s.total}` },
              { key: 'status', header: 'Status', render: (s: any) => (
                <Badge variant={statusColors[s.status] || 'neutral'}>{s.status.replace('_', ' ')}</Badge>
              )},
              { key: 'actions', header: '', render: (s: any) => (
                <Button variant="ghost" size="sm" onClick={() => setShowDetail(s)}>View</Button>
              )},
            ]}
            data={sales || []}
            keyExtractor={(s) => s.id}
            onRowClick={(s) => setShowDetail(s)}
            emptyMessage={
              hasFilters ? 'No sales match these filters' : 'No sales found'
            }
          />
        )}
      </Card>

      {showDetail && (
        <SaleDetailModal
          sale={showDetail}
          onClose={() => setShowDetail(null)}
          onRefund={(data) => refundMutation.mutate(data)}
          onVoid={(data) => voidMutation.mutate(data)}
          isLoading={refundMutation.isPending || voidMutation.isPending}
        />
      )}
    </div>
  );
}

function SaleDetailModal({ sale, onClose, onRefund, onVoid, isLoading }: {
  sale: any;
  onClose: () => void;
  onRefund: (data: any) => void;
  onVoid: (data: any) => void;
  isLoading: boolean;
}) {
  const [activeTab, setActiveTab] = useState<'details' | 'refund' | 'void'>('details');
  const [refundForm, setRefundForm] = useState({ line_id: '', quantity: 1, reason: '', restock: true });
  const [voidReason, setVoidReason] = useState('');
  const { data: settings } = useQuery({ queryKey: ['settings'], queryFn: getSettings });

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Sale ${sale.receipt_number}`}
      size="lg"
    >
      <div className="mb-4 flex gap-2 border-b border-surface-100">
        {(['details', 'refund', 'void'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-surface-400 hover:text-surface-600'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'details' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-surface-400">Receipt:</span> {sale.receipt_number}</div>
            <div><span className="text-surface-400">Date:</span> {formatDateTime(sale.created_at)}</div>
            <div><span className="text-surface-400">Status:</span> <Badge variant="success">{sale.status}</Badge></div>
            <div><span className="text-surface-400">Total:</span> UGX {sale.total}</div>
          </div>
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-surface-600">Receipt</h4>
            <Button variant="secondary" size="sm" onClick={() => window.print()}>
              Print Receipt
            </Button>
          </div>
          <div className="flex justify-center rounded border border-surface-200 bg-surface-50 py-4">
            <Receipt sale={sale} business={settings} />
          </div>
        </div>
      )}

      {activeTab === 'refund' && (
        <div className="space-y-4">
          <p className="text-sm text-surface-400">Refundable amount: UGX {sale.refundable_amount || sale.total}</p>
          <Select
            label="Line Item"
            value={refundForm.line_id}
            onChange={(e) => setRefundForm({ ...refundForm, line_id: e.target.value })}
            options={sale.lines.map((l: any) => ({ value: l.id, label: `${l.product_name} (${l.quantity} sold)` }))}
          />
          <Input label="Quantity" type="number" value={refundForm.quantity} onChange={(e) => setRefundForm({ ...refundForm, quantity: parseInt(e.target.value) })} />
          <Input label="Reason" value={refundForm.reason} onChange={(e) => setRefundForm({ ...refundForm, reason: e.target.value })} required />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={refundForm.restock} onChange={(e) => setRefundForm({ ...refundForm, restock: e.target.checked })} />
            Restock returned items
          </label>
          <Button onClick={() => onRefund({ sale_id: sale.id, ...refundForm })} disabled={isLoading}>
            {isLoading ? 'Processing...' : 'Issue Refund'}
          </Button>
        </div>
      )}

      {activeTab === 'void' && (
        <div className="space-y-4">
          <p className="text-sm text-warning">Voiding a sale will reverse all stock movements and cannot be undone.</p>
          <Input label="Reason" value={voidReason} onChange={(e) => setVoidReason(e.target.value)} required />
          <Button variant="danger" onClick={() => onVoid({ sale_id: sale.id, reason: voidReason })} disabled={isLoading}>
            {isLoading ? 'Processing...' : 'Void Sale'}
          </Button>
        </div>
      )}
    </Modal>
  );
}

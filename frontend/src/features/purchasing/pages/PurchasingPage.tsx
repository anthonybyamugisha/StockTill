import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  cancelPurchaseOrder,
  createPurchaseOrder,
  createSupplier,
  createSupplierInvoice,
  listPurchaseOrders,
  listSupplierInvoices,
  listSuppliers,
  markPurchaseOrderOrdered,
  PurchaseOrder,
  receivePurchaseOrder,
  recordSupplierInvoicePayment,
  Supplier,
  SupplierInvoice,
  SupplierInvoiceLineInput,
  updateSupplier,
  voidSupplierInvoice,
} from '../api/purchasing';
import { listProducts } from '../../catalog/api/catalog';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { Modal } from '../../../shared/ui/Modal';
import { ConfirmDialog } from '../../../shared/ui/ConfirmDialog';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { formatMoney } from '../../../shared/utils/money';
import { formatDate, todayISO } from '../../../shared/utils/date';

const statusVariants: Record<
  string,
  'neutral' | 'primary' | 'success' | 'error' | 'warning'
> = {
  draft: 'neutral',
  ordered: 'primary',
  received: 'success',
  cancelled: 'error',
  unpaid: 'warning',
  partial: 'primary',
  paid: 'success',
  void: 'error',
};

export function PurchasingPage() {
  const [tab, setTab] = useState<'suppliers' | 'orders' | 'invoices'>('suppliers');

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        <Button
          variant={tab === 'suppliers' ? 'primary' : 'secondary'}
          onClick={() => setTab('suppliers')}
        >
          Suppliers
        </Button>
        <Button
          variant={tab === 'orders' ? 'primary' : 'secondary'}
          onClick={() => setTab('orders')}
        >
          Purchase Orders
        </Button>
        <Button
          variant={tab === 'invoices' ? 'primary' : 'secondary'}
          onClick={() => setTab('invoices')}
        >
          Invoices
        </Button>
      </div>

      {tab === 'suppliers' && <SuppliersTab />}
      {tab === 'orders' && <OrdersTab />}
      {tab === 'invoices' && <InvoicesTab />}
    </div>
  );
}

function SuppliersTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [showForm, setShowForm] = useState(false);

  const { data: suppliers } = useQuery({ queryKey: ['suppliers'], queryFn: () => listSuppliers() });

  const saveMutation = useMutation({
    mutationFn: (data: { id?: string; values: Parameters<typeof createSupplier>[0] }) =>
      data.id ? updateSupplier(data.id, data.values) : createSupplier(data.values),
    onSuccess: (supplier, variables) => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      setShowForm(false);
      setEditing(null);
      toast.success(
        variables.id
          ? `Supplier "${supplier.name}" updated`
          : `Supplier "${supplier.name}" added successfully`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not save supplier')),
  });

  return (
    <Card
      title="Suppliers"
      actions={
        <Button
          onClick={() => {
            setEditing(null);
            setShowForm(true);
          }}
        >
          Add Supplier
        </Button>
      }
    >
      <Table
        columns={[
          { key: 'name', header: 'Name', render: (s: Supplier) => s.name },
          { key: 'contact', header: 'Contact', render: (s: Supplier) => s.contact_name || '—' },
          { key: 'phone', header: 'Phone', render: (s: Supplier) => s.phone || '—' },
          { key: 'email', header: 'Email', render: (s: Supplier) => s.email || '—' },
          {
            key: 'status',
            header: 'Status',
            render: (s: Supplier) => (
              <Badge variant={s.is_active ? 'success' : 'neutral'}>
                {s.is_active ? 'Active' : 'Inactive'}
              </Badge>
            ),
          },
          {
            key: 'actions',
            header: '',
            render: (s: Supplier) => (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setEditing(s);
                  setShowForm(true);
                }}
              >
                Edit
              </Button>
            ),
          },
        ]}
        data={suppliers || []}
        keyExtractor={(s) => s.id}
        emptyMessage="No suppliers yet"
      />

      {showForm && (
        <SupplierForm
          supplier={editing}
          onClose={() => {
            setShowForm(false);
            setEditing(null);
          }}
          onSubmit={(values) => saveMutation.mutate({ id: editing?.id, values })}
          isLoading={saveMutation.isPending}
        />
      )}
    </Card>
  );
}

function SupplierForm({
  supplier,
  onClose,
  onSubmit,
  isLoading,
}: {
  supplier: Supplier | null;
  onClose: () => void;
  onSubmit: (values: {
    name: string;
    contact_name: string;
    email: string;
    phone: string;
    address: string;
  }) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState({
    name: supplier?.name ?? '',
    contact_name: supplier?.contact_name ?? '',
    email: supplier?.email ?? '',
    phone: supplier?.phone ?? '',
    address: supplier?.address ?? '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={supplier ? 'Edit Supplier' : 'Add Supplier'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <Input
          label="Contact Name"
          value={form.contact_name}
          onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
        />
        <Input
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <Input
          label="Phone"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
        />
        <Input
          label="Address"
          value={form.address}
          onChange={(e) => setForm({ ...form, address: e.target.value })}
        />
      </form>
    </Modal>
  );
}

function OrdersTab() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [orderToCancel, setOrderToCancel] = useState<PurchaseOrder | null>(null);

  const { data: orders } = useQuery({ queryKey: ['purchaseOrders'], queryFn: listPurchaseOrders });
  const { data: suppliers } = useQuery({ queryKey: ['suppliers'], queryFn: () => listSuppliers() });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] });
    queryClient.invalidateQueries({ queryKey: ['lowStock'] });
    queryClient.invalidateQueries({ queryKey: ['outOfStock'] });
  };

  const createMutation = useMutation({
    mutationFn: createPurchaseOrder,
    onSuccess: (order) => {
      invalidate();
      setShowForm(false);
      toast.success(`Purchase order ${order.reference || order.id.slice(0, 8)} created`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not create purchase order')),
  });

  const orderMutation = useMutation({
    mutationFn: markPurchaseOrderOrdered,
    onSuccess: (order) => {
      invalidate();
      toast.success(`Purchase order ${order.reference || order.id.slice(0, 8)} marked as ordered`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not order purchase order')),
  });

  const receiveMutation = useMutation({
    mutationFn: receivePurchaseOrder,
    onSuccess: (order) => {
      invalidate();
      toast.success(
        `Purchase order ${order.reference || order.id.slice(0, 8)} received — stock updated`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not receive purchase order')),
  });

  const cancelMutation = useMutation({
    mutationFn: (order: PurchaseOrder) => cancelPurchaseOrder(order.id),
    onSuccess: (_order, cancelled) => {
      invalidate();
      setOrderToCancel(null);
      toast.success(
        `Purchase order ${cancelled.reference || cancelled.id.slice(0, 8)} cancelled`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not cancel purchase order')),
  });

  return (
    <Card
      title="Purchase Orders"
      actions={
        <Button onClick={() => setShowForm(true)} disabled={!(suppliers && suppliers.length)}>
          New Purchase Order
        </Button>
      }
    >
      <Table
        columns={[
          { key: 'reference', header: 'Reference', render: (o) => o.reference || o.id.slice(0, 8) },
          { key: 'supplier', header: 'Supplier', render: (o) => o.supplier_name || '—' },
          {
            key: 'status',
            header: 'Status',
            render: (o) => (
              <Badge variant={statusVariants[o.status] ?? 'neutral'}>{o.status}</Badge>
            ),
          },
          { key: 'lines', header: 'Items', render: (o) => o.lines.length },
          { key: 'total', header: 'Total', render: (o) => `UGX ${o.total}` },
          {
            key: 'actions',
            header: '',
            render: (o) => (
              <div className="flex gap-2">
                {o.status === 'draft' && (
                  <Button size="sm" variant="secondary" onClick={() => orderMutation.mutate(o.id)}>
                    Order
                  </Button>
                )}
                {(o.status === 'draft' || o.status === 'ordered') && (
                  <Button size="sm" onClick={() => receiveMutation.mutate(o.id)}>
                    Receive
                  </Button>
                )}
                {(o.status === 'draft' || o.status === 'ordered') && (
                  <Button size="sm" variant="danger" onClick={() => setOrderToCancel(o)}>
                    Cancel
                  </Button>
                )}
              </div>
            ),
          },
        ]}
        data={orders || []}
        keyExtractor={(o) => o.id}
        emptyMessage="No purchase orders yet"
      />

      {showForm && (
        <PurchaseOrderForm
          suppliers={suppliers || []}
          onClose={() => setShowForm(false)}
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      )}

      <ConfirmDialog
        isOpen={orderToCancel !== null}
        title="Cancel purchase order?"
        message={
          <>
            <p>
              Are you sure you want to cancel{' '}
              <span className="font-medium text-surface-700">
                {orderToCancel?.reference || orderToCancel?.id.slice(0, 8)}
              </span>
              ?
            </p>
            <p className="mt-2">A cancelled order cannot be ordered or received.</p>
          </>
        }
        confirmLabel="Yes, cancel order"
        cancelLabel="Keep order"
        isLoading={cancelMutation.isPending}
        onConfirm={() => {
          if (orderToCancel) cancelMutation.mutate(orderToCancel);
        }}
        onCancel={() => {
          cancelMutation.reset();
          setOrderToCancel(null);
        }}
      />
    </Card>
  );
}

interface DraftLine {
  product_id: string;
  quantity: number;
  unit_cost: string;
}

function PurchaseOrderForm({
  suppliers,
  onClose,
  onSubmit,
  isLoading,
}: {
  suppliers: Supplier[];
  onClose: () => void;
  onSubmit: (data: {
    supplier_id: string;
    reference: string;
    lines: { product_id: string; product_name: string; quantity: number; unit_cost: string }[];
  }) => void;
  isLoading: boolean;
}) {
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => listProducts() });
  const [supplierId, setSupplierId] = useState(suppliers[0]?.id ?? '');
  const [reference, setReference] = useState('');
  const [lines, setLines] = useState<DraftLine[]>([{ product_id: '', quantity: 1, unit_cost: '0' }]);

  const productName = (id: string) => products?.find((p) => p.id === id)?.name ?? '';

  const updateLine = (index: number, patch: Partial<DraftLine>) => {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const valid = lines.filter((line) => line.product_id && line.quantity > 0);
    if (!supplierId || valid.length === 0) return;
    onSubmit({
      supplier_id: supplierId,
      reference,
      lines: valid.map((line) => ({
        product_id: line.product_id,
        product_name: productName(line.product_id),
        quantity: line.quantity,
        unit_cost: line.unit_cost,
      })),
    });
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="New Purchase Order"
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Order'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Select
          label="Supplier"
          value={supplierId}
          onChange={(e) => setSupplierId(e.target.value)}
          options={suppliers.map((s) => ({ value: s.id, label: s.name }))}
        />
        <Input
          label="Reference"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
          placeholder="e.g. PO-001"
        />

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="label mb-0">Lines</span>
            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                setLines((current) => [...current, { product_id: '', quantity: 1, unit_cost: '0' }])
              }
            >
              Add Line
            </Button>
          </div>
          {lines.map((line, index) => (
            <div key={index} className="grid grid-cols-12 gap-2">
              <div className="col-span-5">
                <Select
                  value={line.product_id}
                  onChange={(e) => {
                    const product = products?.find((p) => p.id === e.target.value);
                    updateLine(index, {
                      product_id: e.target.value,
                      unit_cost: product?.buying_cost ?? line.unit_cost,
                    });
                  }}
                  options={[
                    { value: '', label: 'Select product' },
                    ...(products || []).map((p) => ({ value: p.id, label: p.name })),
                  ]}
                />
              </div>
              <div className="col-span-3">
                <Input
                  type="number"
                  min="1"
                  value={line.quantity}
                  onChange={(e) =>
                    updateLine(index, { quantity: parseInt(e.target.value || '0', 10) })
                  }
                />
              </div>
              <div className="col-span-3">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={line.unit_cost}
                  onChange={(e) => updateLine(index, { unit_cost: e.target.value })}
                />
              </div>
              <div className="col-span-1 flex items-center">
                <button
                  type="button"
                  className="text-surface-400 hover:text-error"
                  onClick={() => setLines((current) => current.filter((_, i) => i !== index))}
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      </form>
    </Modal>
  );
}


function InvoicesTab() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentInvoice, setPaymentInvoice] = useState<SupplierInvoice | null>(null);
  const [invoiceToVoid, setInvoiceToVoid] = useState<SupplierInvoice | null>(null);

  const { data: invoices } = useQuery({
    queryKey: ['supplierInvoices'],
    queryFn: () => listSupplierInvoices(),
  });
  const { data: suppliers } = useQuery({ queryKey: ['suppliers'], queryFn: () => listSuppliers() });
  const { data: orders } = useQuery({ queryKey: ['purchaseOrders'], queryFn: listPurchaseOrders });

  const visible = (invoices ?? []).filter(
    (invoice) => !statusFilter || invoice.status === statusFilter,
  );

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['supplierInvoices'] });
  };

  const createMutation = useMutation({
    mutationFn: createSupplierInvoice,
    onSuccess: (invoice) => {
      invalidate();
      setShowForm(false);
      toast.success(`Invoice ${invoice.invoice_number} recorded`);
    },
  });

  const paymentMutation = useMutation({
    mutationFn: ({ id, amount }: { id: string; amount: string }) =>
      recordSupplierInvoicePayment(id, amount),
    onSuccess: (invoice) => {
      invalidate();
      setPaymentInvoice(null);
      toast.success(
        invoice.status === 'paid'
          ? `Invoice ${invoice.invoice_number} fully paid`
          : `Payment recorded for ${invoice.invoice_number}`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not record payment')),
  });

  const voidMutation = useMutation({
    mutationFn: (invoice: SupplierInvoice) => voidSupplierInvoice(invoice.id),
    onSuccess: (invoice) => {
      invalidate();
      setInvoiceToVoid(null);
      toast.success(`Invoice ${invoice.invoice_number} voided`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not void invoice')),
  });

  return (
    <Card
      title="Supplier Invoices"
      actions={
        <div className="flex items-center gap-2">
          <select
            className="input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="unpaid">Unpaid</option>
            <option value="partial">Partially paid</option>
            <option value="paid">Paid</option>
            <option value="void">Void</option>
          </select>
          <Button
            onClick={() => setShowForm(true)}
            disabled={!(suppliers && suppliers.length)}
          >
            Record Invoice
          </Button>
        </div>
      }
    >
      <Table
        columns={[
          {
            key: 'number',
            header: 'Invoice',
            render: (invoice: SupplierInvoice) => (
              <div>
                <p className="font-medium">{invoice.invoice_number}</p>
                <p className="text-xs text-surface-400">{invoice.supplier_name}</p>
              </div>
            ),
          },
          {
            key: 'date',
            header: 'Invoice Date',
            render: (invoice: SupplierInvoice) =>
              invoice.invoice_date ? formatDate(invoice.invoice_date) : '�',
          },
          {
            key: 'due',
            header: 'Due Date',
            render: (invoice: SupplierInvoice) =>
              invoice.due_date ? formatDate(invoice.due_date) : '�',
          },
          {
            key: 'total',
            header: 'Total',
            render: (invoice: SupplierInvoice) => formatMoney(invoice.total),
          },
          {
            key: 'balance',
            header: 'Balance',
            render: (invoice: SupplierInvoice) => formatMoney(invoice.balance),
          },
          {
            key: 'status',
            header: 'Status',
            render: (invoice: SupplierInvoice) => (
              <Badge variant={statusVariants[invoice.status] ?? 'neutral'}>
                {invoice.status}
              </Badge>
            ),
          },
          {
            key: 'actions',
            header: '',
            render: (invoice: SupplierInvoice) => (
              <div className="flex gap-2">
                {invoice.status !== 'paid' && invoice.status !== 'void' && (
                  <Button size="sm" onClick={() => setPaymentInvoice(invoice)}>
                    Pay
                  </Button>
                )}
                {invoice.status === 'unpaid' && (
                  <Button size="sm" variant="danger" onClick={() => setInvoiceToVoid(invoice)}>
                    Void
                  </Button>
                )}
              </div>
            ),
          },
        ]}
        data={visible}
        keyExtractor={(invoice) => invoice.id}
        emptyMessage="No supplier invoices yet"
      />

      {showForm && (
        <InvoiceForm
          suppliers={suppliers || []}
          orders={orders || []}
          onClose={() => {
            createMutation.reset();
            setShowForm(false);
          }}
          onSubmit={(data) => createMutation.mutate(data)}
          error={
            createMutation.error
              ? getApiErrorMessage(createMutation.error, 'Could not record invoice')
              : null
          }
          isLoading={createMutation.isPending}
        />
      )}

      {paymentInvoice && (
        <InvoicePaymentModal
          invoice={paymentInvoice}
          onClose={() => setPaymentInvoice(null)}
          onSubmit={(amount) => paymentMutation.mutate({ id: paymentInvoice.id, amount })}
          isLoading={paymentMutation.isPending}
        />
      )}

      <ConfirmDialog
        isOpen={invoiceToVoid !== null}
        title="Void invoice?"
        message={
          <p>
            Void invoice{' '}
            <span className="font-medium text-surface-700">
              {invoiceToVoid?.invoice_number}
            </span>
            ? This cannot be undone, and only unpaid invoices can be voided.
          </p>
        }
        confirmLabel="Yes, void invoice"
        cancelLabel="Keep invoice"
        isLoading={voidMutation.isPending}
        onConfirm={() => {
          if (invoiceToVoid) voidMutation.mutate(invoiceToVoid);
        }}
        onCancel={() => {
          voidMutation.reset();
          setInvoiceToVoid(null);
        }}
      />
    </Card>
  );
}

interface InvoiceDraftLine {
  product_id: string;
  description: string;
  quantity: number;
  unit_cost: string;
}

function InvoiceForm({
  suppliers,
  orders,
  onClose,
  onSubmit,
  error,
  isLoading,
}: {
  suppliers: Supplier[];
  orders: PurchaseOrder[];
  onClose: () => void;
  onSubmit: (data: {
    supplier_id: string;
    invoice_number: string;
    invoice_date: string;
    due_date: string | null;
    purchase_order_id: string | null;
    notes: string;
    lines: SupplierInvoiceLineInput[];
  }) => void;
  error: string | null;
  isLoading: boolean;
}) {
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: () => listProducts() });
  const [supplierId, setSupplierId] = useState(suppliers[0]?.id ?? '');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [invoiceDate, setInvoiceDate] = useState(todayISO());
  const [dueDate, setDueDate] = useState('');
  const [purchaseOrderId, setPurchaseOrderId] = useState('');
  const [notes, setNotes] = useState('');
  const [lines, setLines] = useState<InvoiceDraftLine[]>([
    { product_id: '', description: '', quantity: 1, unit_cost: '0' },
  ]);

  const updateLine = (index: number, patch: Partial<InvoiceDraftLine>) => {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const valid = lines.filter(
      (line) =>
        line.quantity > 0 &&
        (line.product_id || line.description.trim() || line.unit_cost !== '0'),
    );
    if (!supplierId || !invoiceNumber.trim() || valid.length === 0) return;
    onSubmit({
      supplier_id: supplierId,
      invoice_number: invoiceNumber.trim(),
      invoice_date: invoiceDate,
      due_date: dueDate || null,
      purchase_order_id: purchaseOrderId || null,
      notes,
      lines: valid.map((line) => {
        const product = products?.find((candidate) => candidate.id === line.product_id);
        return {
          product_id: line.product_id || null,
          product_name: product?.name ?? '',
          description: line.description,
          quantity: line.quantity,
          unit_cost: line.unit_cost,
        };
      }),
    });
  };

  const total = lines.reduce(
    (sum, line) => sum + (Number(line.unit_cost) || 0) * (line.quantity || 0),
    0,
  );

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Record Supplier Invoice"
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isLoading || !supplierId || !invoiceNumber.trim()}
          >
            {isLoading ? 'Saving...' : 'Record Invoice'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Supplier"
            value={supplierId}
            onChange={(event) => setSupplierId(event.target.value)}
            options={suppliers.map((supplier) => ({
              value: supplier.id,
              label: supplier.name,
            }))}
          />
          <Input
            label="Invoice Number"
            value={invoiceNumber}
            onChange={(event) => setInvoiceNumber(event.target.value)}
            required
          />
          <Input
            label="Invoice Date"
            type="date"
            value={invoiceDate}
            onChange={(event) => setInvoiceDate(event.target.value)}
          />
          <Input
            label="Due Date"
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
          />
          <div className="col-span-2">
            <Select
              label="Purchase Order (optional)"
              value={purchaseOrderId}
              onChange={(event) => setPurchaseOrderId(event.target.value)}
              options={[
                { value: '', label: 'No linked purchase order' },
                ...orders.map((order) => ({
                  value: order.id,
                  label: `${order.reference || order.id.slice(0, 8)} � ${order.supplier_name}`,
                })),
              ]}
            />
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="label mb-0">Invoice Lines</span>
            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                setLines((current) => [
                  ...current,
                  { product_id: '', description: '', quantity: 1, unit_cost: '0' },
                ])
              }
            >
              Add Line
            </Button>
          </div>
          {lines.map((line, index) => (
            <div key={index} className="grid grid-cols-12 gap-2">
              <div className="col-span-3">
                <Select
                  value={line.product_id}
                  onChange={(event) => {
                    const product = products?.find(
                      (candidate) => candidate.id === event.target.value,
                    );
                    updateLine(index, {
                      product_id: event.target.value,
                      unit_cost: product?.buying_cost ?? line.unit_cost,
                    });
                  }}
                  options={[
                    { value: '', label: 'Custom line' },
                    ...(products || []).map((product) => ({
                      value: product.id,
                      label: product.name,
                    })),
                  ]}
                />
              </div>
              <div className="col-span-4">
                <Input
                  placeholder="Description"
                  value={line.description}
                  onChange={(event) => updateLine(index, { description: event.target.value })}
                />
              </div>
              <div className="col-span-2">
                <Input
                  type="number"
                  min="1"
                  value={line.quantity}
                  onChange={(event) =>
                    updateLine(index, { quantity: parseInt(event.target.value) || 0 })
                  }
                />
              </div>
              <div className="col-span-2">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={line.unit_cost}
                  onChange={(event) => updateLine(index, { unit_cost: event.target.value })}
                />
              </div>
              <div className="col-span-1 flex items-center">
                <button
                  type="button"
                  className="text-surface-400 hover:text-error"
                  onClick={() =>
                    setLines((current) => current.filter((_, i) => i !== index))
                  }
                  disabled={lines.length === 1}
                >
                  �
                </button>
              </div>
            </div>
          ))}
          <p className="text-right text-sm text-surface-500">
            Invoice total: {formatMoney(total)}
          </p>
        </div>

        <Input label="Notes" value={notes} onChange={(event) => setNotes(event.target.value)} />
      </form>
    </Modal>
  );
}

function InvoicePaymentModal({
  invoice,
  onClose,
  onSubmit,
  isLoading,
}: {
  invoice: SupplierInvoice;
  onClose: () => void;
  onSubmit: (amount: string) => void;
  isLoading: boolean;
}) {
  const [amount, setAmount] = useState(invoice.balance);
  const numericAmount = Number(amount);
  const invalid = !Number.isFinite(numericAmount) || numericAmount <= 0 || numericAmount > Number(invoice.balance);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!invalid) onSubmit(amount);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={`Record Payment � ${invoice.invoice_number}`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || invalid}>
            {isLoading ? 'Saving...' : 'Record Payment'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="rounded-md bg-surface-50 p-3 text-sm text-surface-500">
          <p>Invoice total: {formatMoney(invoice.total)}</p>
          <p>Already paid: {formatMoney(invoice.amount_paid)}</p>
          <p className="font-medium text-surface-700">Outstanding: {formatMoney(invoice.balance)}</p>
        </div>
        <Input
          label="Payment Amount"
          type="number"
          min="0.01"
          step="0.01"
          max={invoice.balance}
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          required
        />
        {invalid && (
          <p role="alert" className="text-xs text-error">
            Enter an amount greater than zero and no more than the outstanding balance.
          </p>
        )}
      </form>
    </Modal>
  );
}

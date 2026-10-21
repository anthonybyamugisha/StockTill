import { apiClient } from '../../../shared/http/client';

export interface Supplier {
  id: string;
  name: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  is_active: boolean;
  created_at: string;
}

export interface PurchaseOrderLine {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_cost: string;
  line_total: string;
}

export interface PurchaseOrder {
  id: string;
  supplier_id: string | null;
  supplier_name: string;
  status: string;
  reference: string;
  notes: string;
  total: string;
  created_at: string;
  ordered_at: string | null;
  received_at: string | null;
  lines: PurchaseOrderLine[];
}

export interface SupplierInput {
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
}

export interface PurchaseOrderLineInput {
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_cost: string;
}

export async function listSuppliers(search?: string): Promise<Supplier[]> {
  const res = await apiClient.get<Supplier[]>('/purchasing/suppliers/', {
    params: search ? { search } : undefined,
  });
  return res.data;
}

export async function createSupplier(data: SupplierInput): Promise<Supplier> {
  const res = await apiClient.post<Supplier>('/purchasing/suppliers/', data);
  return res.data;
}

export async function updateSupplier(id: string, data: SupplierInput): Promise<Supplier> {
  const res = await apiClient.patch<Supplier>(`/purchasing/suppliers/${id}/`, data);
  return res.data;
}

export async function listPurchaseOrders(): Promise<PurchaseOrder[]> {
  const res = await apiClient.get<PurchaseOrder[]>('/purchasing/orders/');
  return res.data;
}

export async function createPurchaseOrder(data: {
  supplier_id: string;
  reference?: string;
  notes?: string;
  lines: PurchaseOrderLineInput[];
}): Promise<PurchaseOrder> {
  const res = await apiClient.post<PurchaseOrder>('/purchasing/orders/', data);
  return res.data;
}

export async function markPurchaseOrderOrdered(id: string): Promise<PurchaseOrder> {
  const res = await apiClient.post<PurchaseOrder>(`/purchasing/orders/${id}/order/`);
  return res.data;
}

export async function receivePurchaseOrder(id: string): Promise<PurchaseOrder> {
  const res = await apiClient.post<PurchaseOrder>(`/purchasing/orders/${id}/receive/`);
  return res.data;
}

export async function cancelPurchaseOrder(id: string, reason = ''): Promise<PurchaseOrder> {
  const res = await apiClient.post<PurchaseOrder>(`/purchasing/orders/${id}/cancel/`, { reason });
  return res.data;
}

export interface SupplierInvoiceLine {
  id: string;
  product_id: string | null;
  product_name: string;
  description: string;
  quantity: number;
  unit_cost: string;
  line_total: string;
}

export interface SupplierInvoice {
  id: string;
  supplier_id: string | null;
  supplier_name: string;
  invoice_number: string;
  invoice_date: string | null;
  due_date: string | null;
  purchase_order_id: string | null;
  status: string;
  notes: string;
  amount_paid: string;
  total: string;
  balance: string;
  created_at: string;
  lines: SupplierInvoiceLine[];
}

export interface SupplierInvoiceLineInput {
  product_id?: string | null;
  product_name?: string;
  description?: string;
  quantity: number;
  unit_cost: string;
}

export interface SupplierInvoiceInput {
  supplier_id: string;
  invoice_number: string;
  invoice_date?: string | null;
  due_date?: string | null;
  purchase_order_id?: string | null;
  notes?: string;
  lines: SupplierInvoiceLineInput[];
}

export async function listSupplierInvoices(filters: {
  status?: string;
  supplierId?: string;
} = {}): Promise<SupplierInvoice[]> {
  const res = await apiClient.get<SupplierInvoice[]>('/purchasing/invoices/', {
    params: {
      status: filters.status || undefined,
      supplier_id: filters.supplierId || undefined,
    },
  });
  return res.data;
}

export async function createSupplierInvoice(data: SupplierInvoiceInput): Promise<SupplierInvoice> {
  const res = await apiClient.post<SupplierInvoice>('/purchasing/invoices/', data);
  return res.data;
}

export async function recordSupplierInvoicePayment(
  id: string,
  amount: string,
): Promise<SupplierInvoice> {
  const res = await apiClient.post<SupplierInvoice>(`/purchasing/invoices/${id}/payments/`, {
    amount,
  });
  return res.data;
}

export async function voidSupplierInvoice(id: string, reason = ''): Promise<SupplierInvoice> {
  const res = await apiClient.post<SupplierInvoice>(`/purchasing/invoices/${id}/void/`, {
    reason,
  });
  return res.data;
}

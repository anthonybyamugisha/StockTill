import { apiClient } from '../../../shared/http/client';

export interface CashMovement {
  id: string;
  type: string;
  amount: string;
  reason: string;
  created_at: string;
}

export interface Shift {
  id: string;
  cashier_id: string;
  status: string;
  opening_float: string;
  counted_cash: string | null;
  notes: string;
  opened_at: string;
  closed_at: string | null;
  cash_movements: CashMovement[];
}

export interface ShiftReport {
  shift: Shift;
  cash_sales: string;
  cash_refunds: string;
  net_cash_movements: string;
  expected_cash: string;
  counted_cash: string | null;
  variance: string | null;
}

export async function getCurrentShift(): Promise<Shift | null> {
  const res = await apiClient.get<{ shift: Shift | null }>('/shifts/current/');
  return res.data.shift;
}

export async function openShift(data: {
  opening_float: string;
  notes?: string;
}): Promise<Shift> {
  const res = await apiClient.post<Shift>('/shifts/open/', data);
  return res.data;
}

export async function closeShift(data: {
  shift_id: string;
  counted_cash: string;
  notes?: string;
}): Promise<ShiftReport> {
  const res = await apiClient.post<ShiftReport>('/shifts/close/', data);
  return res.data;
}

export async function recordCashMovement(data: {
  shift_id: string;
  type: 'payout' | 'cash_in';
  amount: string;
  reason?: string;
}): Promise<CashMovement> {
  const res = await apiClient.post<CashMovement>('/shifts/cash-movement/', data);
  return res.data;
}

export async function getShiftReport(shiftId: string): Promise<ShiftReport> {
  const res = await apiClient.get<ShiftReport>(`/shifts/${shiftId}/`);
  return res.data;
}

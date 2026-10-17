import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getCurrentShift,
  getShiftReport,
  openShift,
  closeShift,
  recordCashMovement,
  ShiftReport,
} from '../api/shifts';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Badge } from '../../../shared/ui/Badge';
import { Table } from '../../../shared/ui/Table';
import { Modal } from '../../../shared/ui/Modal';
import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';

function money(value: string | null) {
  if (value === null) return '—';
  return `UGX ${value}`;
}

export function ShiftsPage() {
  const queryClient = useQueryClient();
  const [showMovement, setShowMovement] = useState(false);
  const [showClose, setShowClose] = useState(false);
  const [closedReport, setClosedReport] = useState<ShiftReport | null>(null);

  const { data: shift } = useQuery({ queryKey: ['currentShift'], queryFn: getCurrentShift });

  const { data: report } = useQuery({
    queryKey: ['shiftReport', shift?.id],
    queryFn: () => getShiftReport(shift!.id),
    enabled: !!shift,
  });

  const openMutation = useMutation({
    mutationFn: openShift,
    onSuccess: (opened) => {
      queryClient.invalidateQueries({ queryKey: ['currentShift'] });
      toast.success(`Shift opened with a float of ${money(opened.opening_float)}`);
    },
  });

  const movementMutation = useMutation({
    mutationFn: recordCashMovement,
    onSuccess: (movement) => {
      queryClient.invalidateQueries({ queryKey: ['currentShift'] });
      queryClient.invalidateQueries({ queryKey: ['shiftReport'] });
      setShowMovement(false);
      toast.success(
        `${movement.type === 'payout' ? 'Payout' : 'Cash in'} of ${money(movement.amount)} recorded`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not record the cash movement')),
  });

  const closeMutation = useMutation({
    mutationFn: closeShift,
    onSuccess: (result) => {
      setClosedReport(result);
      setShowClose(false);
      queryClient.invalidateQueries({ queryKey: ['currentShift'] });
      const variance = Number(result.variance ?? 0);
      toast.success(
        variance === 0
          ? 'Shift closed — the drawer balanced'
          : `Shift closed — variance of ${money(result.variance)}`,
      );
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not close the shift')),
  });

  if (!shift) {
    return (
      <div className="space-y-6">
        {closedReport && <ClosedReport report={closedReport} />}
        <Card title="Open a shift" subtitle="Count your opening float to start trading">
          <OpenShiftForm
            onSubmit={(data) => openMutation.mutate(data)}
            isLoading={openMutation.isPending}
            error={openMutation.error}
          />
        </Card>
      </div>
    );
  }

  const expected = report?.expected_cash ?? shift.opening_float;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-surface-400">Opening Float</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">{money(shift.opening_float)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Cash Sales</p>
          <p className="mt-1 text-2xl font-semibold text-success">{money(report?.cash_sales ?? null)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Cash Movements</p>
          <p className="mt-1 text-2xl font-semibold text-surface-600">
            {money(report?.net_cash_movements ?? null)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-surface-400">Expected in Drawer</p>
          <p className="mt-1 text-2xl font-semibold text-primary-600">{money(expected)}</p>
        </div>
      </div>

      <Card
        title="Current shift"
        subtitle={`Opened ${new Date(shift.opened_at).toLocaleString()}`}
        actions={
          <>
            <Button variant="secondary" onClick={() => setShowMovement(true)}>
              Record Cash Movement
            </Button>
            <Button variant="danger" onClick={() => setShowClose(true)}>
              Close Shift
            </Button>
          </>
        }
      >
        <div className="mb-4 flex items-center gap-2">
          <span className="text-sm text-surface-400">Status</span>
          <Badge variant="success">Open</Badge>
        </div>
        <Table
          columns={[
            {
              key: 'type',
              header: 'Type',
              render: (m) => (
                <Badge variant={m.type === 'payout' ? 'warning' : 'primary'}>
                  {m.type === 'payout' ? 'Payout' : 'Cash In'}
                </Badge>
              ),
            },
            { key: 'amount', header: 'Amount', render: (m) => money(m.amount) },
            { key: 'reason', header: 'Reason', render: (m) => m.reason || '—' },
            {
              key: 'created_at',
              header: 'Time',
              render: (m) => new Date(m.created_at).toLocaleTimeString(),
            },
          ]}
          data={shift.cash_movements || []}
          keyExtractor={(m) => m.id}
          emptyMessage="No cash movements recorded"
        />
      </Card>

      {closedReport && <ClosedReport report={closedReport} />}

      {showMovement && (
        <CashMovementModal
          onClose={() => setShowMovement(false)}
          onSubmit={(data) => movementMutation.mutate({ shift_id: shift.id, ...data })}
          isLoading={movementMutation.isPending}
        />
      )}

      {showClose && (
        <CloseShiftModal
          onClose={() => setShowClose(false)}
          onSubmit={(data) => closeMutation.mutate({ shift_id: shift.id, ...data })}
          isLoading={closeMutation.isPending}
        />
      )}
    </div>
  );
}

function OpenShiftForm({
  onSubmit,
  isLoading,
  error,
}: {
  onSubmit: (data: { opening_float: string; notes: string }) => void;
  isLoading: boolean;
  error: unknown;
}) {
  const [form, setForm] = useState({ opening_float: '0', notes: '' });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-md space-y-4">
      {!!error && (
        <p className="rounded bg-error/10 px-3 py-2 text-sm text-error">
          {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            'Could not open shift'}
        </p>
      )}
      <Input
        label="Opening Float (UGX)"
        type="number"
        min="0"
        step="0.01"
        value={form.opening_float}
        onChange={(e) => setForm({ ...form, opening_float: e.target.value })}
        required
      />
      <Input
        label="Notes"
        value={form.notes}
        onChange={(e) => setForm({ ...form, notes: e.target.value })}
      />
      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Opening...' : 'Open Shift'}
      </Button>
    </form>
  );
}

function CashMovementModal({
  onClose,
  onSubmit,
  isLoading,
}: {
  onClose: () => void;
  onSubmit: (data: { type: 'payout' | 'cash_in'; amount: string; reason: string }) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState<{ type: 'payout' | 'cash_in'; amount: string; reason: string }>({
    type: 'payout',
    amount: '0',
    reason: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Record Cash Movement"
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
        <Select
          label="Type"
          value={form.type}
          onChange={(e) => setForm({ ...form, type: e.target.value as 'payout' | 'cash_in' })}
          options={[
            { value: 'payout', label: 'Payout (cash out)' },
            { value: 'cash_in', label: 'Cash In (float top-up)' },
          ]}
        />
        <Input
          label="Amount (UGX)"
          type="number"
          min="0"
          step="0.01"
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
          required
        />
        <Input
          label="Reason"
          value={form.reason}
          onChange={(e) => setForm({ ...form, reason: e.target.value })}
          required
        />
      </form>
    </Modal>
  );
}

function CloseShiftModal({
  onClose,
  onSubmit,
  isLoading,
}: {
  onClose: () => void;
  onSubmit: (data: { counted_cash: string; notes: string }) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState({ counted_cash: '0', notes: '' });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Close Shift"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Closing...' : 'Close Shift'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Counted Cash in Drawer (UGX)"
          type="number"
          min="0"
          step="0.01"
          value={form.counted_cash}
          onChange={(e) => setForm({ ...form, counted_cash: e.target.value })}
          required
        />
        <Input
          label="Notes"
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
        />
      </form>
    </Modal>
  );
}

function ClosedReport({ report }: { report: ShiftReport }) {
  const variance = report.variance ?? '0';
  const balanced = Number(variance) === 0;

  return (
    <Card title="Shift closed (Z-report)" subtitle={report.shift.notes || undefined}>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Figure label="Cash Sales" value={money(report.cash_sales)} />
        <Figure label="Cash Refunds" value={money(report.cash_refunds)} />
        <Figure label="Expected" value={money(report.expected_cash)} />
        <Figure label="Counted" value={money(report.counted_cash)} />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <span className="text-sm text-surface-400">Variance</span>
        <Badge variant={balanced ? 'success' : 'error'}>
          {balanced ? 'Balanced' : money(variance)}
        </Badge>
      </div>
    </Card>
  );
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-surface-400">{label}</p>
      <p className="mt-1 text-lg font-semibold text-surface-600">{value}</p>
    </div>
  );
}

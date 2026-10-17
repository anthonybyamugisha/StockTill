import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { completeSale, CompleteSaleRequest, PaymentInput, CartItem } from '../api/pos';
import { queueSale } from '../offline/saleQueue';
import { isNetworkError } from '../offline/networkError';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { formatMoney } from '../../../shared/utils/money';
import { Modal } from '../../../shared/ui/Modal';
import { Button } from '../../../shared/ui/Button';

const paymentSchema = z.object({
  tendered: z.string().optional(),
});

type PaymentFormData = z.infer<typeof paymentSchema>;

interface PaymentResult {
  receipt_number: string;
  queued: boolean;
}

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  total: number;
  onComplete: () => void;
}

export function PaymentModal({ isOpen, onClose, items, total, onComplete }: PaymentModalProps) {
  const { register, handleSubmit, watch } = useForm<PaymentFormData>({
    resolver: zodResolver(paymentSchema),
    defaultValues: { tendered: '' },
  });
  const queryClient = useQueryClient();
  const [result, setResult] = useState<PaymentResult | null>(null);

  const tenderedInput = watch('tendered') ?? '';
  const tenderedValue = parseFloat(tenderedInput);
  const hasTendered = tenderedInput.trim() !== '' && Number.isFinite(tenderedValue);
  const shortfall = hasTendered && tenderedValue < total;
  const change = hasTendered && tenderedValue >= total ? tenderedValue - total : 0;

  const mutation = useMutation({
    mutationFn: async (data: PaymentFormData): Promise<PaymentResult> => {
      const payment: PaymentInput = { method: 'cash', amount: total.toFixed(2) };
      const tendered = data.tendered?.trim();
      if (tendered) payment.tendered = Number(tendered).toFixed(2);

      const payload: CompleteSaleRequest = {
        lines: items.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity,
          unit_price: i.unit_price,
          unit_cost: i.unit_cost,
        })),
        payments: [payment],
        idempotency_key: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      };

      try {
        const sale = await completeSale(payload);
        return { receipt_number: sale.receipt_number, queued: false };
      } catch (error) {
        if (isNetworkError(error)) {
          queueSale(payload);
          return { receipt_number: 'PENDING', queued: true };
        }
        throw error;
      }
    },
    onSuccess: (completed) => {
      setResult(completed);
      queryClient.invalidateQueries();
    },
  });

  if (result) {
    return (
      <Modal isOpen={isOpen} onClose={onComplete} title={result.queued ? 'Sale Saved Offline' : 'Sale Complete'}>
        <div className="text-center py-8">
          <div
            className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full ${
              result.queued ? 'bg-amber-100' : 'bg-green-100'
            }`}
          >
            {result.queued ? (
              <svg className="h-8 w-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
          {result.queued ? (
            <>
              <p className="text-lg font-semibold text-surface-600">Saved for later</p>
              <p className="mt-1 text-sm text-surface-400">
                No connection. This sale is stored on the device and will be sent automatically
                when the connection returns.
              </p>
            </>
          ) : (
            <p className="text-lg font-semibold text-surface-600">Receipt: {result.receipt_number}</p>
          )}
          <Button onClick={onComplete} className="mt-4">New Sale</Button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Payment"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit((data) => mutation.mutate(data))}
            disabled={mutation.isPending || shortfall}
          >
            {mutation.isPending ? 'Processing...' : 'Complete Sale'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        <div className="rounded-lg bg-surface-50 px-4 py-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-surface-500">Amount due</span>
            <span className="text-xl font-semibold text-surface-600">{formatMoney(total)}</span>
          </div>
          <p className="mt-1 text-xs text-surface-400">Cash payment</p>
        </div>

        <div>
          <label className="label">Amount Tendered</label>
          <input
            type="number"
            step="0.01"
            inputMode="decimal"
            {...register('tendered')}
            className="input"
            placeholder={total.toFixed(2)}
          />
          {shortfall && !mutation.error && (
            <p className="mt-1 text-xs text-error">
              Tendered is less than the amount due.
            </p>
          )}
          {change > 0 && (
            <div className="mt-2 flex items-center justify-between rounded bg-green-50 px-3 py-2 text-sm text-green-700">
              <span>Change</span>
              <span className="font-semibold">{formatMoney(change)}</span>
            </div>
          )}
        </div>

        {mutation.error && (
          <div className="rounded bg-red-50 px-3 py-2 text-sm text-error">
            {getApiErrorMessage(mutation.error)}
          </div>
        )}
      </form>
    </Modal>
  );
}

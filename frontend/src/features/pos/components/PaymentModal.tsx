import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { completeSale, CartItem } from '../api/pos';
import { Modal } from '../../../shared/ui/Modal';
import { Button } from '../../../shared/ui/Button';

const paymentSchema = z.object({
  method: z.enum(['cash', 'mobile_money', 'card', 'bank_transfer']),
  tendered: z.string().optional(),
  reference: z.string().optional(),
  provider: z.string().optional(),
});

type PaymentFormData = z.infer<typeof paymentSchema>;

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  total: number;
  onComplete: () => void;
}

export function PaymentModal({ isOpen, onClose, items, total, onComplete }: PaymentModalProps) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<PaymentFormData>({
    resolver: zodResolver(paymentSchema),
    defaultValues: { method: 'cash' },
  });

  const method = watch('method');
  const [receipt, setReceipt] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: PaymentFormData) =>
      completeSale({
        lines: items.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity,
          unit_price: i.unit_price,
          unit_cost: i.unit_cost,
        })),
        payments: [{
          method: data.method,
          amount: total.toFixed(2),
          tendered: data.tendered,
          reference: data.reference,
          provider: data.provider,
        }],
        idempotency_key: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      }),
    onSuccess: (sale) => {
      setReceipt(sale.receipt_number);
    },
  });

  if (receipt) {
    return (
      <Modal isOpen={isOpen} onClose={onComplete} title="Sale Complete">
        <div className="text-center py-8">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-lg font-semibold text-surface-600">Receipt: {receipt}</p>
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
          <Button onClick={handleSubmit((data) => mutation.mutate(data))} disabled={mutation.isPending}>
            {mutation.isPending ? 'Processing...' : 'Complete Sale'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        <div>
          <label className="label">Payment Method</label>
          <div className="grid grid-cols-2 gap-2">
            {(['cash', 'mobile_money', 'card', 'bank_transfer'] as const).map((m) => (
              <label
                key={m}
                className={`flex items-center gap-2 rounded border px-3 py-2 cursor-pointer transition-colors ${
                  method === m ? 'border-primary-500 bg-primary-50' : 'border-surface-200 hover:bg-surface-50'
                }`}
              >
                <input type="radio" value={m} {...register('method')} className="sr-only" />
                <span className="text-sm capitalize">{m.replace('_', ' ')}</span>
              </label>
            ))}
          </div>
        </div>

        {method === 'cash' && (
          <div>
            <label className="label">Amount Tendered</label>
            <input
              type="number"
              step="0.01"
              {...register('tendered')}
              className="input"
              placeholder={total.toFixed(2)}
            />
            {errors.tendered && <p className="mt-1 text-xs text-error">{errors.tendered.message}</p>}
          </div>
        )}

        {(method === 'mobile_money' || method === 'card' || method === 'bank_transfer') && (
          <>
            {method === 'mobile_money' && (
              <div>
                <label className="label">Provider</label>
                <input {...register('provider')} className="input" placeholder="e.g. MTN, Airtel" />
              </div>
            )}
            <div>
              <label className="label">Reference</label>
              <input {...register('reference')} className="input" placeholder="Transaction reference" />
            </div>
          </>
        )}

        {mutation.error && (
          <div className="rounded bg-red-50 px-3 py-2 text-sm text-error">
            {(mutation.error as Error).message}
          </div>
        )}
      </form>
    </Modal>
  );
}

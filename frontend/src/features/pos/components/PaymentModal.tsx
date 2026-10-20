import { FormEvent, useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  completeSale,
  CompleteSaleRequest,
  getSale,
  PaymentInput,
  CartItem,
  Sale,
} from '../api/pos';
import { queueSale } from '../offline/saleQueue';
import { isNetworkError } from '../offline/networkError';
import { getApiErrorMessage } from '../../../shared/http/errors';
import { formatMoney } from '../../../shared/utils/money';
import { Modal } from '../../../shared/ui/Modal';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { Receipt } from '../../../shared/ui/Receipt';
import { toast } from '../../../shared/ui/toast';
import { useAuth } from '../../auth/hooks/useAuth';
import { getSettings } from '../../settings/api/settings';
import { PaymentMethodSelector } from '../../payments/components/PaymentMethodSelector';
import { MobileMoneyForm } from '../../payments/components/MobileMoneyForm';
import { PaymentStatusPanel } from '../../payments/components/PaymentStatusPanel';
import { usePaymentIntent } from '../../payments/hooks/usePaymentIntent';
import { MobileNetwork, PaymentMethod, paymentMethodLabel } from '../../payments/lib/paymentMethods';
import { isFailure, isNeedsReview } from '../../payments/lib/intentStatus';
import {
  calculateChange,
  normalizePhone,
  validatePhone,
  validateTendered,
} from '../../payments/lib/validation';

interface PaymentResult {
  receipt_number: string;
  queued: boolean;
  sale: Sale | null;
}

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  total: number;
  onComplete: () => void;
}

interface SaleInput {
  method: 'cash';
  tendered?: string;
}

function newIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function PaymentModal({ isOpen, onClose, items, total, onComplete }: PaymentModalProps) {
  const queryClient = useQueryClient();
  const [method, setMethod] = useState<PaymentMethod>('cash');
  const [tendered, setTendered] = useState('');
  const [phone, setPhone] = useState('');
  const [network, setNetwork] = useState<MobileNetwork>('mtn');
  const [formError, setFormError] = useState<string | null>(null);
  const [result, setResult] = useState<PaymentResult | null>(null);
  const idempotencyKey = useRef(newIdempotencyKey());
  const paymentIntent = usePaymentIntent();
  const { user } = useAuth();
  const cashierName = user ? `${user.first_name} ${user.last_name}`.trim() : '';
  const { data: settings } = useQuery({ queryKey: ['settings'], queryFn: getSettings });

  const saleLines = items.map((item) => ({
    product_id: item.product_id,
    product_name: item.name,
    quantity: item.quantity,
    unit_price: item.unit_price,
    unit_cost: item.unit_cost,
    discount_type: item.discount_type || null,
    discount_value: item.discount_value || null,
  }));

  const tenderedError = tendered.trim() ? validateTendered(tendered, total) : null;
  const change = calculateChange(tendered, total);

  const saleMutation = useMutation({
    mutationFn: async (input: SaleInput): Promise<PaymentResult> => {
      const payment: PaymentInput = { method: input.method, amount: total.toFixed(2) };

      const cashTendered = input.tendered?.trim();
      if (cashTendered) payment.tendered = Number(cashTendered).toFixed(2);

      const payload: CompleteSaleRequest = {
        lines: saleLines,
        payments: [payment],
        idempotency_key: idempotencyKey.current,
      };

      try {
        const sale = await completeSale(payload);
        return { receipt_number: sale.receipt_number, queued: false, sale };
      } catch (error) {
        if (isNetworkError(error)) {
          queueSale(payload);
          return { receipt_number: 'PENDING', queued: true, sale: null };
        }
        throw error;
      }
    },
    onSuccess: (completed) => {
      setResult(completed);
      queryClient.invalidateQueries();
      if (completed.queued) {
        toast.info('No connection — the sale was saved on this device and will sync automatically');
      } else {
        toast.success(`Sale ${completed.receipt_number} completed`);
      }
    },
  });

  const intent = paymentIntent.intent;
  const saleId = intent?.sale_id ?? null;
  const saleQuery = useQuery({
    queryKey: ['sale', saleId],
    queryFn: () => getSale(saleId as string),
    enabled: intent?.status === 'paid' && saleId !== null,
    retry: 2,
  });

  useEffect(() => {
    if (!saleQuery.data || result) return;
    setResult({
      receipt_number: saleQuery.data.receipt_number,
      queued: false,
      sale: saleQuery.data,
    });
    queryClient.invalidateQueries();
    toast.success(`Sale ${saleQuery.data.receipt_number} completed`);
  }, [saleQuery.data, result, queryClient]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setFormError(null);

    if (method === 'cash') {
      const error = validateTendered(tendered, total);
      if (error) {
        setFormError(error);
        return;
      }
      saleMutation.mutate({ method, tendered });
      return;
    }

    const error = validatePhone(phone);
    if (error) {
      setFormError(error);
      return;
    }
    paymentIntent.start({
      method: 'mobile_money',
      amount: total.toFixed(2),
      phone: normalizePhone(phone),
      network,
      idempotency_key: idempotencyKey.current,
      sale: { lines: saleLines },
    });
  };

  const handleMethodChange = (next: PaymentMethod) => {
    setMethod(next);
    setFormError(null);
  };

  const handleRetry = () => {
    idempotencyKey.current = newIdempotencyKey();
    setFormError(null);
    paymentIntent.reset();
  };

  const handleClose = () => {
    if (intent?.status === 'pending') {
      paymentIntent.cancel();
    }
    onClose();
  };

  if (result) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onComplete}
        title={result.queued ? 'Sale Saved Offline' : 'Sale Complete'}
        footer={
          result.queued ? (
            <Button onClick={onComplete}>New Sale</Button>
          ) : (
            <>
              <Button variant="secondary" onClick={onComplete}>New Sale</Button>
              <Button onClick={() => window.print()}>Print Receipt</Button>
            </>
          )
        }
      >
        <div className="py-2 text-center">
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
            <>
              <p className="text-lg font-semibold text-surface-600">Receipt: {result.receipt_number}</p>
              <p className="mt-1 text-sm text-surface-400">
                Print the receipt for the customer, then start the next sale.
              </p>
            </>
          )}
        </div>

        {!result.queued && result.sale && (
          <div className="mt-4 flex justify-center border-t border-surface-100 pt-4">
            <Receipt sale={result.sale} business={settings} cashierName={cashierName} />
          </div>
        )}
      </Modal>
    );
  }

  const busy = saleMutation.isPending || paymentIntent.isStarting;
  const settled = intent !== null && (isFailure(intent.status) || isNeedsReview(intent.status));
  const footer = intent ? (
    settled ? (
      <Button variant="secondary" onClick={onClose}>Close</Button>
    ) : null
  ) : (
    <>
      <Button variant="secondary" onClick={handleClose}>Cancel</Button>
      <Button type="submit" form="payment-form" disabled={busy}>
        {busy
          ? 'Processing...'
          : method === 'mobile_money'
            ? 'Send Payment Request'
            : 'Complete Sale'}
      </Button>
    </>
  );

  const intentError =
    intent?.status === 'paid' && saleId === null
      ? 'Payment received, but no sale was linked. Ask a manager to review it.'
      : saleQuery.error
        ? getApiErrorMessage(saleQuery.error, 'Payment received, but the receipt could not be loaded.')
        : paymentIntent.error;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Payment" footer={footer}>
      {intent ? (
        <PaymentStatusPanel
          intent={intent}
          error={intentError}
          isCancelling={paymentIntent.isCancelling}
          onCancel={paymentIntent.cancel}
          onRetry={handleRetry}
        />
      ) : (
        <form id="payment-form" onSubmit={handleSubmit} className="space-y-4">
          <div className="rounded-lg bg-surface-50 px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-surface-500">Amount due</span>
              <span className="text-xl font-semibold text-surface-600">{formatMoney(total)}</span>
            </div>
            <p className="mt-1 text-xs text-surface-400">
              {method === 'mobile_money'
                ? 'The customer approves the payment on their phone'
                : `${paymentMethodLabel(method)} payment`}
            </p>
          </div>

          <PaymentMethodSelector
            value={method}
            onChange={handleMethodChange}
            disabled={busy}
          />

          {method === 'cash' && (
            <div>
              <Input
                label="Amount Tendered"
                type="number"
                step="0.01"
                inputMode="decimal"
                value={tendered}
                onChange={(event) => setTendered(event.target.value)}
                placeholder={total.toFixed(2)}
                disabled={busy}
              />
              {tenderedError && (
                <p className="mt-1 text-xs text-error">{tenderedError}</p>
              )}
              {change > 0 && (
                <div className="mt-2 flex items-center justify-between rounded bg-green-50 px-3 py-2 text-sm text-green-700">
                  <span>Change</span>
                  <span className="font-semibold">{formatMoney(change)}</span>
                </div>
              )}
            </div>
          )}

          {method === 'mobile_money' && (
            <MobileMoneyForm
              phone={phone}
              onPhoneChange={setPhone}
              network={network}
              onNetworkChange={setNetwork}
              amount={total}
              disabled={busy}
              error={formError}
            />
          )}

          {formError && method !== 'mobile_money' && (
            <div className="rounded bg-red-50 px-3 py-2 text-sm text-error">{formError}</div>
          )}

          {saleMutation.error && (
            <div className="rounded bg-red-50 px-3 py-2 text-sm text-error">
              {getApiErrorMessage(saleMutation.error)}
            </div>
          )}
        </form>
      )}
    </Modal>
  );
}

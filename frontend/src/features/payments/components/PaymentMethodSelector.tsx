import { PAYMENT_METHOD_OPTIONS, PaymentMethod } from '../lib/paymentMethods';

interface PaymentMethodSelectorProps {
  value: PaymentMethod;
  onChange: (method: PaymentMethod) => void;
  disabled?: boolean;
}

export function PaymentMethodSelector({
  value,
  onChange,
  disabled = false,
}: PaymentMethodSelectorProps) {
  return (
    <div role="radiogroup" aria-label="Payment method" className="grid grid-cols-2 gap-2">
      {PAYMENT_METHOD_OPTIONS.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={`rounded-lg border px-3 py-2 text-left transition ${
              selected
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-surface-200 text-surface-600 hover:border-surface-300'
            } disabled:cursor-not-allowed disabled:opacity-60`}
          >
            <span className="block text-sm font-medium">{option.label}</span>
            <span className="mt-0.5 block text-xs text-surface-400">{option.description}</span>
          </button>
        );
      })}
    </div>
  );
}

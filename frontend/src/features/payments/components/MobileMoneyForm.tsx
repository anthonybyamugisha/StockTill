import { Input } from '../../../shared/ui/Input';
import { formatMoney } from '../../../shared/utils/money';
import { MobileNetwork, MOBILE_NETWORK_OPTIONS } from '../lib/paymentMethods';

interface MobileMoneyFormProps {
  phone: string;
  onPhoneChange: (phone: string) => void;
  network: MobileNetwork;
  onNetworkChange: (network: MobileNetwork) => void;
  amount: number;
  disabled?: boolean;
  error?: string | null;
}

export function MobileMoneyForm({
  phone,
  onPhoneChange,
  network,
  onNetworkChange,
  amount,
  disabled = false,
  error,
}: MobileMoneyFormProps) {
  return (
    <div className="space-y-3">
      <Input
        label="Customer phone number"
        type="tel"
        inputMode="tel"
        placeholder="0772 123 456"
        value={phone}
        onChange={(event) => onPhoneChange(event.target.value)}
        disabled={disabled}
        error={error ?? undefined}
        autoComplete="off"
      />
      <div>
        <p className="label">Network</p>
        <div
          role="radiogroup"
          aria-label="Mobile money network"
          className="grid grid-cols-2 gap-2"
        >
          {MOBILE_NETWORK_OPTIONS.map((option) => {
            const selected = option.value === network;
            return (
              <button
                key={option.value}
                type="button"
                role="radio"
                aria-checked={selected}
                disabled={disabled}
                onClick={() => onNetworkChange(option.value)}
                className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                  selected
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-surface-200 text-surface-600 hover:border-surface-300'
                } disabled:cursor-not-allowed disabled:opacity-60`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>
      <p className="text-xs text-surface-400">
        The customer will get a prompt to approve {formatMoney(amount)} on their phone.
      </p>
    </div>
  );
}

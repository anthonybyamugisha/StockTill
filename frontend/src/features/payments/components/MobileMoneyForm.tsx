import { Input } from '../../../shared/ui/Input';
import { Select } from '../../../shared/ui/Select';
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
      <Select
        label="Network"
        value={network}
        onChange={(event) => onNetworkChange(event.target.value as MobileNetwork)}
        options={MOBILE_NETWORK_OPTIONS}
        disabled={disabled}
      />
      <p className="text-xs text-surface-400">
        The customer will get a prompt to approve {formatMoney(amount)} on their phone.
      </p>
    </div>
  );
}

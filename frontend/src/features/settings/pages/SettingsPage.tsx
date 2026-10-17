import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';
import { BusinessSettings, getSettings, updateSettings } from '../api/settings';
import { toast } from '../../../shared/ui/toast';
import { getApiErrorMessage } from '../../../shared/http/errors';

const defaults: BusinessSettings = {
  business_name: '',
  address: '',
  phone: '',
  email: '',
  currency: 'UGX',
  receipt_header: '',
  receipt_footer: '',
  cashier_discount_limit: '0',
  tax_rate: '0',
  logo_url: null,
};

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ['settings'], queryFn: getSettings });
  const [form, setForm] = useState<BusinessSettings>(defaults);

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: (saved) => {
      setForm(saved);
      queryClient.setQueryData(['settings'], saved);
      toast.success('Settings saved');
    },
    onError: (error) => toast.error(getApiErrorMessage(error, 'Could not save settings')),
  });

  return (
    <div className="max-w-2xl space-y-6">
      <Card title="Business Settings">
        <div className="grid grid-cols-2 gap-4">
          <Input label="Business Name" value={form.business_name} onChange={(e) => setForm({ ...form, business_name: e.target.value })} />
          <Input label="Currency" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
          <div className="col-span-2">
            <Input label="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </div>
          <Input label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <Input label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
      </Card>

      <Card title="Receipt Settings">
        <div className="space-y-4">
          <Input label="Receipt Header" value={form.receipt_header} onChange={(e) => setForm({ ...form, receipt_header: e.target.value })} />
          <Input label="Receipt Footer" value={form.receipt_footer} onChange={(e) => setForm({ ...form, receipt_footer: e.target.value })} />
        </div>
      </Card>

      <Card title="POS Settings">
        <div className="grid grid-cols-2 gap-4">
          <Input label="Cashier Discount Limit (%)" type="number" value={form.cashier_discount_limit} onChange={(e) => setForm({ ...form, cashier_discount_limit: e.target.value })} />
          <Input label="Tax Rate (%)" type="number" value={form.tax_rate} onChange={(e) => setForm({ ...form, tax_rate: e.target.value })} />
        </div>
      </Card>

      <div className="flex items-center justify-end gap-3">
        <Button onClick={() => mutation.mutate(form)} disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}

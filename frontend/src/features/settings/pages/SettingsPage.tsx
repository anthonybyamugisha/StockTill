import { useState } from 'react';
import { Card } from '../../../shared/ui/Card';
import { Button } from '../../../shared/ui/Button';
import { Input } from '../../../shared/ui/Input';

export function SettingsPage() {
  const [form, setForm] = useState({
    business_name: 'StockTill Shop',
    address: '123 Main Street, Kampala',
    phone: '+256 700 000 000',
    email: 'info@stocktill.com',
    currency: 'UGX',
    receipt_header: 'Thank you for shopping with us!',
    receipt_footer: 'Returns accepted within 7 days with receipt',
    cashier_discount_limit: '10',
    tax_rate: '0',
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

      <div className="flex justify-end">
        <Button>Save Settings</Button>
      </div>
    </div>
  );
}

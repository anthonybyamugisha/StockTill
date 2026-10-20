import { describe, expect, it } from 'vitest';
import {
  buildReceiptText,
  lineTotal,
  methodLabel,
  money,
  providerLabel,
  ReceiptSale,
  round2,
} from './receipt';

const sale: ReceiptSale = {
  receipt_number: 'ST-2026-000001',
  created_at: '2026-10-17T10:30:00Z',
  status: 'completed',
  lines: [
    { product_name: 'Rice 5kg', quantity: 2, unit_price: '25000.00', total: '50000.00' },
    {
      product_name: 'Sugar 1kg',
      quantity: 1,
      unit_price: '5000.00',
      discount_amount: '500.00',
      total: '4500.00',
    },
  ],
  payments: [{ method: 'cash', amount: '54500.00', tendered: '60000.00', change: '5500.00' }],
  subtotal: '55000.00',
  total_discount: '500.00',
  total: '54500.00',
  amount_paid: '54500.00',
};

describe('round2', () => {
  it('rounds to two decimals', () => {
    expect(round2(1.005)).toBe(1.01);
    expect(round2(2.344)).toBe(2.34);
  });
});

describe('methodLabel', () => {
  it('maps known methods to friendly labels', () => {
    expect(methodLabel('cash')).toBe('Cash');
    expect(methodLabel('mobile_money')).toBe('Mobile Money');
    expect(methodLabel('bank_transfer')).toBe('Bank Transfer');
  });

  it('title-cases unknown methods', () => {
    expect(methodLabel('store_credit')).toBe('Store Credit');
  });
});

describe('providerLabel', () => {
  it('maps the mobile money networks', () => {
    expect(providerLabel('mtn')).toBe('MTN MoMo');
    expect(providerLabel('airtel')).toBe('Airtel Money');
  });

  it('labels a manual payment and title-cases unknown providers', () => {
    expect(providerLabel('manual')).toBe('Manual');
    expect(providerLabel('card_terminal')).toBe('Card Terminal');
  });
});

describe('money', () => {
  it('formats a value with the currency prefix and two decimals', () => {
    expect(money('25000', 'UGX')).toBe('UGX 25000.00');
    expect(money(5000, 'USD')).toBe('USD 5000.00');
  });

  it('treats an invalid value as zero', () => {
    expect(money('not-a-number')).toBe('UGX 0.00');
  });
});

describe('lineTotal', () => {
  it('uses the stored total when present', () => {
    expect(lineTotal({ product_name: 'Rice', quantity: 2, unit_price: '100', total: '180' })).toBe(180);
  });

  it('computes quantity times unit price minus discount when no total', () => {
    expect(
      lineTotal({ product_name: 'Sugar', quantity: 3, unit_price: '100', discount_amount: '50' }),
    ).toBe(250);
  });
});

describe('buildReceiptText', () => {
  const business = {
    business_name: 'StockTill Shop',
    address: 'Kampala Road',
    phone: '+256 700 000000',
    currency: 'UGX',
    receipt_header: 'VAT No 123',
    receipt_footer: 'Thank you!',
  };

  it('includes the store, receipt number and each product with quantity and unit price', () => {
    const text = buildReceiptText(sale, business, 'Anthony');
    expect(text).toContain('StockTill Shop');
    expect(text).toContain('VAT No 123');
    expect(text).toContain('ST-2026-000001');
    expect(text).toContain('Anthony');
    expect(text).toContain('Rice 5kg');
    expect(text).toContain('2 x UGX 25000.00');
    expect(text).toContain('Sugar 1kg');
    expect(text).toContain('1 x UGX 5000.00');
  });

  it('shows the totals, discount, payment, tendered and change', () => {
    const text = buildReceiptText(sale, business);
    expect(text).toContain('Subtotal');
    expect(text).toContain('UGX 55000.00');
    expect(text).toContain('Discount');
    expect(text).toContain('-UGX 500.00');
    expect(text).toContain('TOTAL');
    expect(text).toContain('UGX 54500.00');
    expect(text).toContain('Cash');
    expect(text).toContain('Tendered');
    expect(text).toContain('UGX 60000.00');
    expect(text).toContain('Change');
    expect(text).toContain('UGX 5500.00');
    expect(text).toContain('Thank you!');
  });

  it('falls back to a default footer when none is configured', () => {
    const text = buildReceiptText({ ...sale, status: 'completed' });
    expect(text).toContain('Thank you for shopping with us!');
    expect(text).toContain('StockTill');
  });

  it('flags a non-completed sale', () => {
    const text = buildReceiptText({ ...sale, status: 'voided' });
    expect(text).toContain('Status: voided');
  });

  it('shows the network and reference for a mobile money payment', () => {
    const text = buildReceiptText(
      {
        ...sale,
        payments: [
          {
            method: 'mobile_money',
            amount: '54500.00',
            provider: 'mtn',
            reference: 'MP240101.1234.A56789',
          },
        ],
      },
      business,
    );
    expect(text).toContain('Mobile Money');
    expect(text).toContain('Provider');
    expect(text).toContain('MTN MoMo');
    expect(text).toContain('Reference');
    expect(text).toContain('MP240101.1234.A56789');
  });

  it('shows a manual reference for a card payment', () => {
    const text = buildReceiptText({
      ...sale,
      payments: [{ method: 'card', amount: '54500.00', provider: 'manual', reference: 'SLIP-42' }],
    });
    expect(text).toContain('Card');
    expect(text).toContain('Manual');
    expect(text).toContain('SLIP-42');
  });
});

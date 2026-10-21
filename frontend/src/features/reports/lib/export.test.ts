import { describe, expect, it } from 'vitest';

import { reportExport } from './export';

describe('reportExport', () => {
  it('exports the transaction list from the sales tab', () => {
    expect(reportExport('sales')).toEqual({
      path: '/reporting/sales-report/csv/',
      filename: 'sales_report.csv',
      dated: true,
    });
  });

  it('leaves the date range out of undated reports', () => {
    expect(reportExport('inventory')?.dated).toBe(false);
    expect(reportExport('lowstock')?.dated).toBe(false);
  });

  it('exports payment method sales', () => {
    expect(reportExport('payments')).toEqual({
      path: '/reporting/by-payment-method/csv/',
      filename: 'sales_by_payment_method.csv',
      dated: true,
    });
  });

  it('returns nothing for an unknown report', () => {
    expect(reportExport('unknown')).toBeUndefined();
  });
});

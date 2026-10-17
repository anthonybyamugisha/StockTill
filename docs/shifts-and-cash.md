# Shifts and cash-drawer reconciliation

A shift is a cashier's trading session at a till. StockTill uses shifts to
reconcile the cash drawer: you count the float when you open, the system tracks
every cash sale, refund and manual movement during the session, and you count
the drawer again when you close to see the variance.

## Concepts

- **Opening float** — the cash placed in the drawer when the shift opens.
- **Cash movement** — a manual adjustment to the drawer:
  - `payout` — cash taken out (transport, supplier, petty cash). Reduces expected cash.
  - `cash_in` — cash added (float top-up, change brought in). Increases expected cash.
- **Expected cash** — `opening_float + cash_sales - cash_refunds + net cash movements`.
- **Counted cash** — the physical amount you count at closing.
- **Variance** — `counted_cash - expected_cash`. Zero means the drawer balances.
- **X-report** — the figures for an open shift (running totals).
- **Z-report** — the figures captured when a shift is closed, with the variance.

## API

All endpoints require authentication and are scoped to the current cashier.

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/api/v1/shifts/current/` | The current cashier's open shift (or `null`) |
| POST | `/api/v1/shifts/open/` | Open a shift (`opening_float`, optional `notes`) |
| POST | `/api/v1/shifts/cash-movement/` | Record a movement (`shift_id`, `type`, `amount`, `reason`) |
| POST | `/api/v1/shifts/close/` | Close a shift (`shift_id`, `counted_cash`, optional `notes`) |
| GET  | `/api/v1/shifts/{id}/` | X-report for an open shift or Z-report for a closed one |

A cashier can only have one open shift at a time; opening a second one returns
`400`. Sales completed while a shift is open are stamped with its `shift_id`, so
the report's cash totals come from the sales actually rung up during the session.

Example: open a shift and close it with a shortage.

```bash
curl -X POST https://stocktill.onrender.com/api/v1/shifts/open/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"opening_float": "100000.00"}'

curl -X POST https://stocktill.onrender.com/api/v1/shifts/close/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"shift_id": "<id>", "counted_cash": "99000.00"}'
# => expected_cash 100000.00, counted_cash 99000.00, variance -1000.00
```

## Frontend

The **Shifts** page (sidebar → Shifts, available to cashiers, managers and
admins) shows the current shift: opening float, cash sales, net movements and
the expected amount in the drawer. From there you can:

1. Open a shift by entering the opening float.
2. Record payouts and cash-in movements with a reason.
3. Close the shift by counting the drawer — the Z-report then shows the
   expected versus counted cash and the variance.

## Design notes

- The `shifts` bounded context owns `Shift` and `CashMovement`. It never reads
  the sales tables directly; it asks the `sales` context for cash totals through
  the `SalesSummaryPort` (implemented by `SalesSummaryAdapter`).
- Conversely, `sales` resolves the open shift for a cashier through its own
  `ShiftPort` (`ShiftAdapter`), keeping the dependency between contexts explicit
  and one-directional at the port level.
- `Shift.close()` is idempotent-guarded: closing an already-closed shift raises
  `ShiftAlreadyClosedError`.

# ADR 0002: Append-Only Stock Ledger

## Status

Accepted

## Context

Stock changes need full auditability. We must know who changed what, when, and why.

## Decision

All stock changes are recorded as immutable StockMovement rows. The current stock on hand is derived from the ledger and cached in StockItem for performance.

## Consequences

- Full audit trail of every stock change
- Cache can be rebuilt from ledger at any time
- DB constraint prevents negative stock
- Slightly more writes, but reads are fast

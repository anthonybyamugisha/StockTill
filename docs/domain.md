# Domain Glossary

| Term | Definition |
|------|-----------|
| **Sale** | A completed transaction with a receipt number, lines, and payments |
| **Sale Line** | A single product within a sale, with quantity, price snapshot, and optional discount |
| **Payment** | A payment against a sale (cash, mobile money, card, bank transfer) |
| **Refund** | A partial or full reversal of a sale, with reason and optional restock |
| **Void** | A full cancellation of a completed sale |
| **Stock Movement** | An append-only ledger entry recording a stock change |
| **Stock Item** | Cached on-hand quantity derived from the movement ledger |
| **Money** | Decimal-based value object (UGX), never float |
| **Idempotency Key** | Client-generated key preventing duplicate sale creation |
| **Unit of Work** | Database transaction boundary |
| **Port** | Interface declared by a use case for cross-context communication |
| **Adapter** | Infrastructure implementation of a port |

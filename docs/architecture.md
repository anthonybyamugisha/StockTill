# StockTill Architecture

## Overview

StockTill is a modular monolith backend with Clean Architecture / DDD, paired with a React SPA frontend.

## Bounded Contexts

- **accounts** — users, roles, authentication
- **catalog** — products, categories, SKUs
- **inventory** — stock ledger, movements, valuation
- **sales** — sales, payments, refunds, voids, receipts
- **reporting** — read-only queries, dashboards, exports

## Layers (per context)

1. **Domain** — pure Python entities, aggregates, value objects, domain events, repository interfaces. No Django imports.
2. **Application** — use cases (commands/queries), ports for cross-context communication.
3. **Infrastructure** — Django ORM models, migrations, repository implementations, adapters.
4. **Interfaces** — DRF views, serializers, permissions, URLs.

## Dependency Rule

Dependencies point inward. Domain has no framework imports. Contexts never import each other's models. Cross-context calls go through ports/adapters.

Enforced by import-linter in CI.

## Frontend

React SPA organized by feature folder. Talks only to `/api/v1/` via a shared axios client. Role-based route guards.

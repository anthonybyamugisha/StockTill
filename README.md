# StockTill

Browser-based Point of Sale and inventory management system for retail shops.

## Features

- **POS** — Fast cashier interface with product search, cart, discounts, split payments, and receipt printing
- **Inventory** — Append-only stock ledger, low-stock alerts, valuation, adjustments
- **Sales Management** — Search, filter, refund, void, reprint receipts
- **Dashboard** — Real-time KPIs, charts, best sellers, payment breakdown
- **Reports** — Sales, profit, inventory, cashier, low stock — with CSV export
- **Users & Roles** — Admin, Manager, Cashier with role-based permissions
- **Audit Log** — Track every change in the system

## Tech Stack

**Backend:** Python 3.12, Django, Django REST Framework, PostgreSQL

**Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts

**Testing:** pytest, factory_boy, hypothesis, Vitest, Playwright

**Infrastructure:** Docker, GitHub Actions, Sentry

## Quick Start

```bash
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs/ |

## Project Structure

```
backend/
  accounts/      Users, roles, authentication
  catalog/       Products, categories
  inventory/     Stock ledger, movements, valuation
  sales/         Sales, payments, refunds, voids
  reporting/     Dashboard queries, reports, CSV export
  settings/      Business configuration
  shared/        Money, entities, UoW, audit

frontend/src/
  app/           Router, layout, providers
  features/      One folder per capability (pos, catalog, sales, ...)
  shared/        HTTP client, UI components, utils
  e2e/           Playwright tests
```

## Development

```bash
make up          # Start all services
make test        # Run backend and frontend tests
make lint        # Lint backend
make typecheck   # Type check both sides
```

## Architecture

Clean Architecture / DDD modular monolith. Each bounded context has four layers: Domain, Application, Infrastructure, Interfaces. Dependencies point inward. Cross-context calls go through ports and adapters.

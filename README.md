# StockTill

Browser-based Point of Sale and inventory management system for retail shops.

## Features

- **POS** — Fast cashier interface with product search, cart, discounts, split payments, and receipt printing
- **Barcode Scanning** — USB/Bluetooth scanners, camera scanning, and manual entry on the cashier screen
- **Inventory** — Append-only stock ledger, low-stock alerts, valuation, adjustments
- **Purchasing** — Suppliers and purchase orders; receiving an order adds stock to inventory
- **Sales Management** — Search, filter, refund, void, reprint receipts
- **Shifts & Cash** — Open/close shifts, record payouts and float top-ups, reconcile the drawer with an X/Z report
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
  shifts/        Shifts, cash movements, drawer reconciliation
  purchasing/    Suppliers, purchase orders, goods receiving
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

## Documentation

- [Architecture](docs/architecture.md)
- [Domain model](docs/domain.md)
- [Deployment](docs/deployment.md)
- [Barcode scanning](docs/barcode-scanning.md)
- [Offline selling and PWA](docs/offline-and-pwa.md)
- [Shifts and cash reconciliation](docs/shifts-and-cash.md)
- [Purchasing and suppliers](docs/purchasing.md)

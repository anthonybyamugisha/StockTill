# StockTill

Browser-based Point of Sale and inventory management system for retail shops. StockTill is a
**modular-monolith** backend (Python 3.12, Django, Django REST Framework) and a **React/TypeScript**
single-page app, built with **Domain-Driven Design**, **Clean Architecture** and **Test-Driven
Development** as first-class engineering disciplines --- not as decoration around a framework.

> This README doubles as the project's engineering documentation: how it is structured, why it is
> structured that way, and how to run, test and deploy it.

## Features

- **POS** --- Fast cashier interface with an on-screen catalogue grid (every available product as a
  tappable tile, category-filtered, showing remaining stock and disabling sold-out items) so nothing
  has to be memorised, plus product search, cart, per-line discounts, split payments, cash
  tendered/change, and a printable receipt (store details, each line's name, quantity and unit price,
  totals, discount, payment, tendered and change) that can also be reprinted from Sales
- **Barcode Scanning** --- USB/Bluetooth keyboard-wedge scanners, camera scanning, and manual entry
  on the cashier screen (no scanner required to run the system)
- **Inventory** --- Append-only stock ledger, opening stock captured when a product is created,
  low-stock alerts, valuation, adjustments, write-offs
- **Purchasing** --- Suppliers and purchase orders; receiving an order adds stock to the ledger
- **Sales Management** --- Search, filter, refund, void, and view receipts
- **Shifts & Cash** --- Open/close shifts, record payouts and float top-ups, reconcile the drawer
  with an X/Z report
- **Offline-first PWA** --- Installable app that keeps selling when the network drops
- **Dashboard** --- Real-time KPIs, the sales trend, and this month's best sellers
- **Reports** --- Sales, profit, inventory, cashier, low stock --- with CSV export
- **Users & Roles** --- Admin, Manager, Cashier with role-based permissions
- **Audit Log** --- An immutable record of who did what and when, with before/after values for
  money- and security-relevant actions (admin-only)

## Tech Stack

**Backend:** Python 3.12, Django, Django REST Framework, PostgreSQL 16

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, axios, Recharts

**Testing:** pytest, pytest-django, factory\_boy, hypothesis, Vitest, Playwright

**Quality:** ruff (lint/format), mypy (strict), import-linter (architecture), one `make` target

**Infrastructure:** Docker, Docker Compose, Gunicorn, WhiteNoise, Sentry

## Quick Start

```bash
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs/ |

## Project Structure

```
StockTill/
│
├─ backend/                                        Django + DRF modular monolith
│  ├─ config/                                      Settings, root URLs, WSGI/ASGI
│  │  └─ settings/                                 Base · dev · test · prod
│  ├─ shared/                                      Cross-cutting kernel
│  │  └─ domain/                                   Money · entities · clock · errors
│  ├─ accounts/  catalog/  inventory/              Eight bounded contexts;
│  ├─ shifts/  sales/  purchasing/                 Each is laid out as:
│  ├─ reporting/  settings/
│  │     ├─ domain/                                Entities, value objects, interfaces
│  │     ├─ application/                           Use cases, commands, ports
│  │     ├─ infrastructure/                        Django models, migrations, adapters
│  │     └─ interfaces/                            DRF views, serializers, urls
│  ├─ manage.py
│  ├─ pyproject.toml                               Ruff · mypy · import-linter · pytest
│  └─ requirements.txt
│
├─ frontend/                                       React + TypeScript SPA (Vite)
│  ├─ src/
│  │  ├─ app/                                      Router, providers, layout, PWA
│  │  ├─ features/                                 One folder per capability
│  │  │  ├─ pos/                                   api · components · hooks · pages
│  │  │  ├─ catalog/  inventory/  sales/  shifts/
│  │  │  ├─ purchasing/  reports/  dashboard/
│  │  │  └─ users/  audit/  auth/  settings/       Same layering as above
│  │  ├─ shared/                                   HTTP client · UI kit · PWA
│  │  └─ App.tsx  main.tsx  index.css
│  ├─ public/                                      Manifest · sw.js · icons
│  ├─ e2e/                                         Playwright specs (auth, POS)
│  └─ vite.config.ts · vercel.json
│
├─ deploy/                                         backup.sh · restore.sh · env.template
├─ docker-compose.yml                              Local dev stack (api · db · web)
├─ Makefile                                        up · test · lint · typecheck
├─ render.yaml                                     Render blueprint                               
```

## Development

```bash
make up          # Start all services
make test        # Run backend and frontend tests
make lint        # Lint backend
make typecheck   # Type check both sides
```

---

# Architecture: why DDD, Clean Architecture and TDD

Frameworks solve *delivery* problems: routing HTTP, mapping rows to objects, rendering screens.
They do not decide **what the business is allowed to do**. In a POS, the rules that actually matter
are things like *"a sale cannot be completed unless payments cover the total"*, *"stock can never go
negative"*, *"an expected drawer balance is float + cash sales − refunds ± movements"* and
*"a purchase order can only be received once"*. Those rules are the asset. If they live inside
Django models, serializers or views, they become entangled with the framework, hard to test in
isolation, and expensive to change.

StockTill therefore **inverts the usual dependency**: the framework depends on the domain, not the
other way around. Below is the reasoning for each discipline, and the concrete evidence in the code.

## 1. Why Domain-Driven Design

**The problem with a framework-first design.** The obvious way to build this in Django is to put
behaviour on `models.Model` subclasses, let the ORM's `save()` define the workflow, and call it a
day. That works until the rules grow: totals with discounts, partial refunds, split payments,
shift reconciliation, partial receiving. At that point the rules are scattered across models,
serializers and views, duplicated, and only testable by standing up a database.

**What we did.** We modelled the business explicitly, in plain Python with no framework imports:

- **Entities & aggregates** --- `Sale`, `Shift`, `PurchaseOrder`, `Supplier`. Each aggregate is the
  only thing allowed to enforce its own invariants.
- **Value objects** --- `Money` is a decimal value object (never `float`), so currency rounding is
  defined in exactly one place.
- **Ubiquitous language** --- the words in the code (*sale line*, *payment*, *refund*, *void*,
  *stock movement*, *shift*, *variance*, *purchase order*) are the words used in the UI, the tests
  and this document.
- **Domain events, repository interfaces, ports** --- declared in the inner layers and satisfied
  outside.

A good example is `Shift.expected_cash()` and `Shift.variance()`: the drawer formula lives on the
aggregate, so the API, the reports and the tests all agree because they call the same method.

## 2. Why Clean Architecture

**The problem with coupling to Django.** ORM models, HTTP serializers and request objects are
*details*. If the domain imports them, then every domain test needs Django, every schema change
ripples into business rules, and the business rules can't be reasoned about without knowing the
framework.

**What we did.** Every bounded context has four layers with a strict inward dependency:

| Layer | Contains | Depends on |
|-------|----------|-----------|
| **Domain** | Entities, aggregates, value objects, domain events, domain errors, repository **interfaces** | Pure Python only --- no Django, no DRF |
| **Application** | Use cases (command/query handlers), **ports** for cross-context work, clocks | Domain |
| **Infrastructure** | Django models, migrations, repository implementations, adapters | Application + Domain |
| **Interfaces** | DRF views, serializers, permissions, URLs | Application |

The rule --- *source code dependencies only point inward* --- is not a convention people must
remember; it is **verified automatically by `import-linter`** (see `backend/pyproject.toml`). Two
contracts run on every quality-gate pass:

1. `*.domain` must not import `django` or `rest_framework`.
2. A context's `application`/`infrastructure` must not import another context, except through
   explicitly whitelisted adapters.

**What this buys us.**

- **The domain is testable at the speed of thought.** The `Sale` and `Shift` rules are exercised by
  hundreds of fast unit tests that never touch a database.
- **Cross-context boundaries are real.** `sales` deducts stock through an `inventory` port;
  `shifts` reads cash totals through a `sales` port; `purchasing` adds stock through a
  `StockIntakePort`. No context imports another's ORM models. Adapters absorb the few unavoidable
  cross-context imports, and those are the only lines the linter allows.
- **Django is replaceable.** Because the ORM sits in the `infrastructure` layer, changing the web
  framework or the persistence engine would not touch a single business rule.

### Bounded contexts

| Context | Responsibility |
|---------|----------------|
| `accounts` | Users, roles, authentication, account lockout, audit log |
| `catalog` | Products, categories, SKUs/barcodes, pricing and cost |
| `inventory` | Append-only stock ledger, on-hand cache, valuation, low/out-of-stock |
| `sales` | Sales aggregate, lines, payments, refunds, voids, receipt numbering |
| `shifts` | Cashier shifts, opening float, cash movements, drawer reconciliation |
| `purchasing` | Suppliers, purchase orders, goods receiving into inventory |
| `reporting` | Read-only projections: dashboards, reports, CSV export |
| `settings` | Business configuration (name, currency, receipt header/footer, discount limit, tax) |

The **modular monolith** choice (ADR-0001) keeps the operational simplicity of a single deployable
unit while preserving the option to extract a context into its own service later.

### Architecture decision records

Design decisions are recorded in the repository history and summarised here:

- **ADR-0001 --- Modular monolith.** Clean boundaries without microservice operational cost; clear
  contexts; single deploy; no distributed-transaction overhead.
- **ADR-0002 --- Append-only stock ledger.** Every stock change is an immutable `StockMovement`; the
  on-hand quantity is derived and cached in `StockItem`. This gives a full audit trail, a cache that
  can be rebuilt from the ledger at any time, and a database constraint that makes negative stock
  impossible.

## 3. Why Test-Driven Development

**The problem with testing after the fact.** When tests are bolted on, they tend to assert whatever
the code happens to do --- including bugs --- and they usually need the whole stack running. The
business rules end up validated only through the slowest, most fragile tests.

**What we did.** TDD at two levels:

- **Domain-first unit tests.** Behaviour is specified before the entities are written. Examples:
  sale totals and discounts, refundable quantities, `Money` rounding, shift expected-cash/variance,
  and purchase-order state transitions. These are fast, deterministic and framework-free.
- **API/contract tests.** DRF tests confirm the HTTP surface, permissions, idempotent replay,
  barcode lookup, shift closing and purchase-order receiving --- the integration points that unit
  tests intentionally ignore.

This split mirrors Clean Architecture: the domain is proven in isolation, the wiring is proven at the
edges. The current suite is **156 backend tests** and **44 frontend unit tests**, plus Playwright
end-to-end scenarios; deepening each context's domain suite is the top item on the roadmap.

## 4. Why this is more than "just Django"

Using the framework is not the point --- using it *at the edges* is. A summary:

| Concern | Framework-first | StockTill |
|---------|-----------------|-----------|
| Where business rules live | ORM models / serializers / views | Domain entities & aggregates (pure Python) |
| How rules are tested | Through the database and HTTP | Fast unit tests, no DB, no HTTP |
| How contexts relate | Direct model imports | Ports & adapters, verified by the linter |
| What changing the DB costs | Rewriting business rules | Swapping infrastructure only |
| What the invariants are | Implicit, scattered | Explicit on the aggregate, one source of truth |

Django, DRF and React still do the heavy lifting --- CRUD, auth plumbing, HTTP, rendering --- but they
are kept *outside* the domain so that the part of the system that earns the shop money is the part we
can reason about, test and change with confidence.

---

# Domain model (glossary)

| Term | Definition |
|------|-----------|
| **Sale** | A completed transaction with a receipt number, lines and payments |
| **Sale Line** | A product within a sale, with quantity, price snapshot and optional discount |
| **Payment** | A payment against a sale (the POS is cash-only; the domain also models mobile money, card and bank transfer) |
| **Refund** | A partial or full reversal of a sale, with reason and optional restock |
| **Void** | A full cancellation of a completed sale |
| **Stock Movement** | An append-only ledger entry recording a stock change |
| **Stock Item** | Cached on-hand quantity derived from the movement ledger |
| **Shift** | A cashier's trading session at a till, with an opening float and reconciliation |
| **Cash Movement** | A manual drawer adjustment during a shift: a payout or a cash-in |
| **Purchase Order** | A request to a supplier, tracked draft/ordered/received/cancelled |
| **Money** | Decimal-based value object (UGX), never `float` |
| **Idempotency Key** | Client-generated key preventing duplicate sale creation |
| **Unit of Work** | Database transaction boundary |
| **Port** | Interface declared by a use case for cross-context communication |
| **Adapter** | Infrastructure implementation of a port |

# Feature notes

### Barcode scanning

The POS adds products by barcode in three ways, and **no scanner is required to run or evaluate the
system**:

1. **USB / Bluetooth scanner** --- a keyboard-wedge ("HID") scanner behaves like a second keyboard.
   The POS listens for a fast burst of characters ending in Enter anywhere on the page, so the
   cashier can scan without focusing a field. Any standard 1D or 2D model works out of the box.
2. **Camera** --- "Scan with camera" decodes via the browser's native `BarcodeDetector` API (Chrome
   and Edge; other browsers show a helpful message). No extra dependency is installed.
3. **Manual entry** --- type six or more characters into the search box and press Enter.

`frontend/src/features/pos/lib/barcodeBuffer.ts` is a small, framework-free buffer that tells a
scanner burst apart from human typing using minimum length, average key interval and an idle reset.

API: `GET /api/v1/catalog/products/by-barcode/?barcode=<code>` (200 active product / 400 missing
parameter / 404 unknown / 403 unauthenticated). Search also matches name, SKU and barcode.

### Offline-first selling and PWA

StockTill is an installable PWA and keeps trading offline:

- **Service worker** (`frontend/public/sw.js`): navigation is network-first with a cached
  `index.html` fallback; static assets are cache-first; **API reads are never cached** because stock
  and prices must be truthful.
- **Offline sale queue** (`frontend/src/features/pos/offline/saleQueue.ts`): when a completed sale
  fails because of a *connection* problem (not a validation error) it is stored in `localStorage`
  keyed by its idempotency key, and the cashier is told it was saved.
- **Replay** (`saleSync.ts`) runs on app start, on the browser `online` event, and from a manual
  "Sync now" action. Because the backend de-duplicates on the idempotency key, a replay that the
  server already processed cannot create a duplicate sale.
- An app-wide banner shows the offline state and how many sales are waiting.

Only sales are queued offline; refunds, adjustments and admin actions require a live connection.

### Shifts and cash-drawer reconciliation

A shift is a cashier's session at a till. You count the opening float when it opens; the system
tracks cash sales, refunds and manual movements (`payout` / `cash_in`); and you count the drawer
again when you close. Expected cash is `float + cash sales − cash refunds ± movements`, and the
variance is `counted − expected`. An **X-report** shows a running total for an open shift; a
**Z-report** captures the figures and variance at close. Sales are stamped with the `shift_id` open
when they were rung up, so cash totals come from the sales actually made during the session. A
cashier can only have one open shift at a time.

API: `/api/v1/shifts/current/`, `/open/`, `/cash-movement/`, `/close/`, and `/{id}/` (report).

### Purchasing and suppliers

Manage suppliers and raise purchase orders with product lines and agreed unit costs. Orders move
**draft → ordered → received** (or → cancelled). Receiving adds each line's quantity to the
inventory ledger through a `StockIntakePort`, so procurement and stock levels stay in step. A
received order cannot be cancelled; an order can only be received once. Product names are captured
on the line at order time so a PO keeps its history even if the catalog entry changes later.

API: `/api/v1/purchasing/suppliers/`, `/suppliers/{id}/`, `/orders/`, `/orders/{id}/`, and the
`/orders/{id}/order/`, `/receive/`, `/cancel/` transitions.

### Audit log

Every money- or security-relevant action writes an immutable entry: **who** (the acting user), **what**
(`action`, `entity_type`, `entity_id`), **when** (timestamp) and the **before/after** values, so a
change can be reconstructed rather than merely noticed. Recorded activity covers:

- **Authentication** --- successful and failed logins, blocked attempts (deactivated/locked), logout.
- **Users** --- created, updated, **role changes**, deactivated.
- **Catalog** --- product created/updated (price changes as before/after diffs) and deactivated;
  category created/deactivated.
- **Inventory** --- opening stock and manual adjustments, each with the on-hand quantity before and
  after. Automatic movements generated by a sale are *not* double-logged; they are captured by the
  `sale.completed` entry, keeping one entry per business action.
- **Sales** --- completed (receipt, total, payment methods), **voided** (with reason), refunded.
- **Shifts** --- opened, closed (with expected cash and variance), and cash movements.
- **Purchasing** --- supplier created/updated; purchase order created/ordered/received/cancelled.
- **Settings** --- business configuration changes, recorded as a diff.

The port (`AuditPort`) is declared in `shared/application/audit.py` and injected into the use cases
that emit events; the Django implementation (`DjangoAuditRepository`) writes to the `accounts` audit
table, so no other context imports the audit model directly. Use cases default to a no-op recorder,
which keeps them testable in isolation. Entries are read-only and exposed through an admin-only view
that resolves the acting user's name and email, colour-codes the action, and renders the change as a
readable `before → after` list with a filter box.

API: `GET /api/v1/accounts/audit-log/` (admin only), optionally filtered by `action`, `entity_type`,
`user_id`, `date_from` and `date_to`.

# Quality and testing

- **Backend:** `ruff check` and `ruff format --check`; `mypy` in `strict` mode over the domain and
  application layers; `import-linter` for the dependency rule; `pytest` (with coverage) against the
  same PostgreSQL 16 engine as production (in-memory SQLite can be substituted for speed).
- **Frontend:** `tsc --noEmit`, Vitest, and a production `vite build`.
- All of the above are reproducible locally with one `make` target and are documented in the
  Makefile; they must pass before code is deployed.

# Security highlights

Session authentication served over HTTPS with HSTS; role-based permission classes (least
privilege); account lockout after repeated failed logins; PBKDF2 password hashing; CSRF protection
with trusted origins; idempotency keys with a unique constraint to prevent duplicate charges; an
append-only **audit log** that records the acting user, the action and the before/after values for
logins, user and role changes, price and stock changes, sales, voids, refunds, shifts, purchasing and
settings (readable only to administrators); and database constraints (non-negative stock, positive
quantities) that make whole classes of errors impossible.

# Deployment

**Environments:** `dev` (Docker Compose, hot reload) · `test` (ephemeral database) · `prod`
(Docker/Gunicorn/WhiteNoise/Sentry).

**Production:** the API runs on Render (Gunicorn + WhiteNoise) with a managed PostgreSQL database;
the SPA is deployed to Vercel. On every deploy the backend runs migrations, seeds the administrator
account, collects static files, then starts Gunicorn. Health check: `GET /api/v1/health/`.

Migrations and backups:

```bash
docker compose run --rm backend python manage.py makemigrations
docker compose run --rm backend python manage.py migrate
./deploy/backup.sh              # pg_dump
./deploy/restore.sh <file.sql>  # restore
```

# License

Released for the competition submission; contact the author for reuse.

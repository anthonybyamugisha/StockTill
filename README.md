# StockTill

Browser-based Point of Sale and inventory management system for retail shops. StockTill is a
**modular-monolith** backend (Python 3.12, Django, Django REST Framework) and a **React/TypeScript**
single-page app, built with **Domain-Driven Design**, **Clean Architecture** and **Test-Driven
Development** as first-class engineering disciplines. They are not decoration around a framework.

## Features

- **POS**. Fast cashier interface with an on-screen catalogue grid (every available product as a
  tappable tile, category-filtered, showing remaining stock and disabling sold-out items) so nothing
  has to be memorised, plus product search, cart, per-line discounts, split payments, cash
  tendered/change, and a printable receipt (store details, each line's name, quantity and unit price,
  totals, discount, payment, tendered and change) that can also be reprinted from Sales
- **Barcode Scanning**. USB/Bluetooth keyboard-wedge scanners, camera scanning, and manual entry
  on the cashier screen (no scanner required to run the system)
- **Catalog**. Products with images and optional category assignment; managers can add, rename,
  parent, deactivate and reactivate categories
- **Inventory**. Append-only stock ledger, opening stock captured when a product is created,
  low-stock and out-of-stock alerts (including products never stocked), valuation, adjustments,
  write-offs and per-product movement history
- **Purchasing**. Suppliers, purchase orders and supplier invoices; receiving an order adds stock
  to the ledger, and invoices track partial and full payments
- **Sales Management**. Search by receipt number, filter by status, payment method, cashier and
  date range, refund, void, reprint receipts
- **Shifts & Cash**. Open/close shifts, record payouts and float top-ups, reconcile the drawer
  with an X/Z report
- **Offline-first PWA**. Installable app that keeps selling when the network drops
- **Dashboard**. Real-time KPIs, the sales trend, this month's best sellers and a 30-day payment mix
- **Reports**. Sales, profit, inventory, best-seller, cashier, payment-method and low-stock reports,
  grouped by the shop's calendar day. Every report tab downloads its own CSV, and an export reports
  its own failures instead of silently downloading an error page
- **Users & Roles**. Admin, Manager, Cashier with role-based permissions; an administrator-issued
  temporary password that the user must replace at first sign-in, and a voluntary password change
  from the header
- **Clear feedback**. Every action confirms itself with a toast (or explains its failure), and
  destructive ones (deactivate, cancel an order, void) ask for confirmation first
- **Audit Log**. An immutable record of who did what and when, with before/after values for
  money- and security-relevant actions (admin-only)

## Tech Stack

**Backend:** Python 3.12, Django, Django REST Framework, PostgreSQL 16

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, axios, Recharts

**Testing:** pytest, pytest-django, factory\_boy, hypothesis, Vitest, Playwright

**Quality:** ruff (lint/format), mypy (strict), architecture tests, one `make` target

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
│  │     │  └─ use_cases/                          One module per operation
│  │     ├─ infrastructure/                        Django models, migrations, adapters
│  │     │  └─ queries/                            One query class per report
│  │     └─ interfaces/                            DRF views, serializers, urls
│  ├─ manage.py
│  ├─ pyproject.toml                               Ruff · mypy · import-linter · pytest
│  └─ requirements.txt
│
├─ frontend/                                       React + TypeScript SPA (Vite)
│  ├─ src/
│  │  ├─ app/                                      Layout, PWA shell
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
├─ deploy/                                         backup.sh · restore.sh · verify_release.py · env.template
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

- **Entities & aggregates**. `Sale`, `Shift`, `PurchaseOrder`, `Supplier`. Each aggregate is the
  only thing allowed to enforce its own invariants.
- **Value objects**. `Money` is a decimal value object (never `float`), so currency rounding is
  defined in exactly one place.
- **Ubiquitous language**. The words in the code (*sale line*, *payment*, *refund*, *void*,
  *stock movement*, *shift*, *variance*, *purchase order*) are the words used in the UI, the tests
  and this document.
- **Repository interfaces and ports**. These are declared in the inner layers and satisfied
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
| **Domain** | Entities, aggregates, value objects, domain errors, repository **interfaces** | Pure Python only. No Django, no DRF |
| **Application** | Use cases (command/query handlers), **ports** for cross-context work, clocks | Domain |
| **Infrastructure** | Django models, migrations, repository implementations, adapters | Application + Domain |
| **Interfaces** | DRF views, serializers, permissions, URLs | Application |

The rule. *Source code dependencies only point inward*. It is declared as two contracts in
`backend/pyproject.toml`:

1. `*.domain` must not import `django` or `rest_framework`.
2. A context's `application`/`infrastructure` must not import another context, except through
   explicitly whitelisted adapters.

The first contract is also enforced by a test (`backend/config/tests/test_domain_purity.py`), so a
stray framework import in a domain module fails the normal test run. The cross-context whitelist is
kept by hand as each adapter is added.

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
| `purchasing` | Suppliers, purchase orders, goods receiving, supplier invoices and payments |
| `reporting` | Read-only projections: dashboards, reports, CSV export |
| `settings` | Business configuration (name, currency, receipt header/footer, discount limit, tax) |

The **modular monolith** choice (ADR-0001) keeps the operational simplicity of a single deployable
unit while preserving the option to extract a context into its own service later.

### Code organisation (SOLID)

The same rules are applied in every context, so it is predictable where a change belongs:

- **One operation per module.** `application/use_cases/` holds a module per workflow
  (`complete_sale.py`, `refund_sale.py`, …) instead of one growing file, so a change to refunds
  cannot accidentally touch checkout.
- **One port per collaboration.** A use case declares only the interface it needs. Cross-context
  work goes through an adapter, and read models use one query class per report
  (`reporting/infrastructure/queries/profit.py`, …) each implementing a single `execute` method.
- **Composition happens at the edge.** Views ask a context's `container.py` for a wired use case
  (`build_refund_sale_use_case()`), so construction never leaks into business logic and tests can
  substitute fakes.
- **Mapping is its own step.** `interfaces/api/request_mapping.py` turns validated input into a
  command, keeping `Decimal`/enum conversion out of the views.
- **Value objects over loose parameters.** `DateRange.from_params` gives every report identical date
  parsing, defaults and shop-day semantics; `Money` replaces floats wherever money moves.
- **Edge behaviour is shared.** `@domain_errors_to_bad_request` maps domain and validation errors to
  `400` in one place instead of a `try/except` in every endpoint.

Adding a report or a workflow therefore means adding a small, independently testable module rather
than editing a class that every feature shares.

### Architecture decision records

Design decisions are recorded in the repository history and summarised here:

- **ADR-0001. Modular monolith.** Clean boundaries without microservice operational cost; clear
  contexts; single deploy; no distributed-transaction overhead.
- **ADR-0002. Append-only stock ledger.** Every stock change is an immutable `StockMovement`; the
  on-hand quantity is derived and cached in `StockItem`. This gives a full audit trail, a cache that
  can be rebuilt from the ledger at any time, and a database constraint that makes negative stock
  impossible.

## 3. Why Test-Driven Development

**The problem with testing after the fact.** When tests are bolted on, they tend to assert whatever
the code happens to do. That includes bugs. They usually need the whole stack running. The
business rules end up validated only through the slowest, most fragile tests.

**What we did.** TDD at two levels:

- **Domain-first unit tests.** Behaviour is specified before the entities are written. Examples:
  sale totals and discounts, refundable quantities, `Money` rounding, shift expected-cash/variance,
  and purchase-order state transitions. These are fast, deterministic and framework-free.
- **API/contract tests.** DRF tests confirm the HTTP surface, permissions, idempotent replay,
  barcode lookup, shift closing and purchase-order receiving. These are the integration points that
  unit tests intentionally ignore.

This split mirrors Clean Architecture: the domain is proven in isolation, the wiring is proven at the
edges. The current suite is **476 backend tests** and **126 frontend unit tests**, plus Playwright
end-to-end scenarios; deepening each context's domain suite is the top item on the roadmap.

## 4. Why this is more than "just Django"

Using the framework is not the point. Using it *at the edges* is. A summary:

| Concern | Framework-first | StockTill |
|---------|-----------------|-----------|
| Where business rules live | ORM models / serializers / views | Domain entities & aggregates (pure Python) |
| How rules are tested | Through the database and HTTP | Fast unit tests, no DB, no HTTP |
| How contexts relate | Direct model imports | Ports & adapters, guarded by tests |
| What changing the DB costs | Rewriting business rules | Swapping infrastructure only |
| What the invariants are | Implicit, scattered | Explicit on the aggregate, one source of truth |

Django, DRF and React still do the heavy lifting. That means CRUD, auth plumbing, HTTP and rendering. But they
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
| **Port** | Interface declared by a use case for cross-context communication |
| **Adapter** | Infrastructure implementation of a port |

# Feature notes

### Barcode scanning

The POS adds products by barcode in three ways, and **no scanner is required to run or evaluate the
system**:

1. **USB / Bluetooth scanner**. A keyboard-wedge ("HID") scanner behaves like a second keyboard.
   The POS listens for a fast burst of characters ending in Enter anywhere on the page, so the
   cashier can scan without focusing a field. Any standard 1D or 2D model works out of the box.
2. **Camera**. "Scan with camera" decodes via the browser's native `BarcodeDetector` API (Chrome
   and Edge; other browsers show a helpful message). No extra dependency is installed.
3. **Manual entry**. Type six or more characters into the search box and press Enter.

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

Supplier invoices are recorded separately from stock receiving. Each invoice belongs to a supplier,
can optionally reference a purchase order, and carries line items and a due date. A payment updates
the invoice from **unpaid → partial → paid**; overpayment is rejected, and only an unpaid invoice can
be voided. Invoice create, payment and void actions are written to the audit log.

API: `/api/v1/purchasing/suppliers/`, `/suppliers/{id}/`, `/orders/`, `/orders/{id}/`, the
`/orders/{id}/order/`, `/receive/`, `/cancel/` transitions, `/invoices/`, `/invoices/{id}/`, and
`/invoices/{id}/payments/`, `/void/`.

### Temporary passwords and first login

An administrator creates a user with a password, but that password is explicitly temporary. The
`must_change_password` flag is set at creation and travels with every user payload. After signing in:

- the SPA sends the user to `/change-password` and keeps every other route behind a redirect; a `403`
  with `code: password_change_required` from any request also redirects the browser there, so a stale
  tab cannot silently retry against a gated endpoint;
- the API rejects every endpoint except `/accounts/login/`, `/accounts/me/`,
  `/accounts/change-password/`, `/accounts/logout/`, the health check and the docs, with a `403`
  carrying `code: password_change_required`. This is enforced server-side by middleware, not by the
  SPA, so a client that skips the screen still cannot use the till. The exempt routes are matched
  exactly, so a lookalike path such as `/accounts/me/extra/` is still gated;
- the replacement must be at least eight characters, mix a letter with a number, and differ from the
  temporary password. The old password stops working immediately; the current session is kept alive
  with `update_session_auth_hash` so the user is not bounced back to the login page. The screen also
  offers a sign-out, so a user handed the wrong account is not stranded;
- the change is audited as `auth.password_changed`, and the flag is cleared in the same database
  write as the new hash.

The rule follows the *first sign-in*, not the account's creation date. A login is treated as a first
login whenever the account has never recorded one (`last_login` is `null`), so an account created
before the flag existed is pulled into the flow the first time it signs in. The sign-in is audited as
`auth.first_login`, and the data migration `accounts/0003_backfill_first_login_passwords` sets the flag
on every existing account that has never signed in. Accounts that have already signed in, and the
seeded superuser, are left alone. The superuser stays exempt so the deployment's break-glass account
remains usable even if its flag is ever set. The temporary password is never stored in plain text or
written to the audit log.

A gated request returns:

```json
{
  "detail": "Change your temporary password before using StockTill.",
  "code": "password_change_required"
}
```

API: `POST /api/v1/accounts/change-password/` with `current_password` and `new_password`.

### Audit log

Every money- or security-relevant action writes an immutable entry: **who** (the acting user), **what**
(`action`, `entity_type`, `entity_id`), **when** (timestamp) and the **before/after** values, so a
change can be reconstructed rather than merely noticed. Recorded activity covers:

- **Authentication**. Successful and failed logins, first sign-ins that trigger a password change,
  blocked attempts (deactivated/locked), logout, and both forced and voluntary password changes.
- **Users**. Created, updated, **role changes**, deactivated.
- **Catalog**. Product created/updated (price changes as before/after diffs) and deactivated;
  category created/updated/deactivated.
- **Inventory**. Opening stock and manual adjustments, each with the on-hand quantity before and
  after. Automatic movements generated by a sale are *not* double-logged; they are captured by the
  `sale.completed` entry, keeping one entry per business action.
- **Sales**. Completed (receipt, total, payment methods), **voided** (with reason), refunded.
- **Shifts**. Opened, closed (with expected cash and variance), and cash movements.
- **Purchasing**. Supplier created/updated; purchase order created/ordered/received/cancelled;
  supplier invoice created/paid/voided.
- **Settings**. Business configuration changes, recorded as a diff.

The port (`AuditPort`) is declared in `shared/application/audit.py` and injected into the use cases
that emit events; the Django implementation (`DjangoAuditRepository`) writes to the `accounts` audit
table, so no other context imports the audit model directly. Use cases default to a no-op recorder,
which keeps them testable in isolation. Entries are read-only and exposed through an admin-only view
that resolves the acting user's name and email, colour-codes the action, and renders the change as a
readable `before → after` list with a filter box.

API: `GET /api/v1/accounts/audit-log/` (admin only), optionally filtered by `action`, `entity_type`,
`user_id`, `date_from` and `date_to`.

### Reporting and the shop day

A sale rung at 00:20 belongs to that day's takings, not the previous one, so every report, dashboard
and CSV export buckets sales by the **shop's calendar day** (`Africa/Kampala`), not by UTC:

- Stored timestamps stay UTC-aware (`USE_TZ = True`); grouping uses `created_at__date`, which Django
  evaluates in the active timezone, and the "today / this week / this month" windows come from
  `timezone.localdate()` rather than `date.today()`, so a UTC container can never shift the shop's day.
- The browser asks for ranges using its own calendar day (`toISODate()`), never
  `toISOString()`-derived dates, which would roll back a day for any UTC+ offset during the small
  hours.
- `daily-sales` returns **every day in the range**, zero-filled, so a trend line shows gaps as zero
  rather than silently connecting across missing days, and charts plot the numbers (money arrives as
  strings from DRF) with short `18 Oct` labels.

Every report tab has a matching download endpoint, and the CSV is produced from the same query
object as the JSON, never from a second SQL path that could drift:

| Report | JSON | CSV |
| --- | --- | --- |
| Sales transactions | `/api/v1/reporting/sales-report/` | `/api/v1/reporting/sales-report/csv/` |
| Sales summary | `/api/v1/reporting/sales-summary/` | `/api/v1/reporting/sales-summary/csv/` |
| Daily sales | `/api/v1/reporting/daily-sales/` | `/api/v1/reporting/daily-sales/csv/` |
| Profit | `/api/v1/reporting/profit/` | `/api/v1/reporting/profit/csv/` |
| Best sellers | `/api/v1/reporting/top-products/` | `/api/v1/reporting/top-products/csv/` |
| Cashier sales | `/api/v1/reporting/cashier-sales/` | `/api/v1/reporting/cashier-sales/csv/` |
| Low stock | `/api/v1/reporting/low-stock/` | `/api/v1/reporting/low-stock/csv/` |
| Inventory | `/api/v1/reporting/inventory/` | `/api/v1/reporting/inventory/csv/` |
| Payment methods | `/api/v1/reporting/by-payment-method/` | `/api/v1/reporting/by-payment-method/csv/` |

All CSV responses use `text/csv` with an `attachment` filename, money is written with two decimals,
and dates are ISO. The undated reports (inventory, low stock) ignore the range; the others accept the
same `date_from` / `date_to` parameters as their JSON counterpart. The reports screen sends the
active tab's name through one mapping, so a tab can never download another tab's data.

# Quality and testing

- **Backend:** `ruff check` and `ruff format --check`; `mypy` in `strict` mode over the domain and
  application layers; `pytest` (with coverage) against the
  same PostgreSQL 16 engine as production (in-memory SQLite can be substituted for speed).
- **Frontend:** `tsc --noEmit`, Vitest, and a production `vite build`.
- All of the above are reproducible locally with one `make` target and are documented in the
  Makefile; they must pass before code is deployed.

# Security highlights

Session authentication served over HTTPS with HSTS; role-based permission classes (least
privilege); account lockout after repeated failed logins; PBKDF2 password hashing; temporary
administrator-issued passwords that must be replaced at first sign-in (enforced by API middleware,
not just the UI); CSRF protection
with trusted origins; idempotency keys with a unique constraint to prevent duplicate charges; an
append-only **audit log** that records the acting user, the action and the before/after values for
logins, user and role changes, price and stock changes, sales, voids, refunds, shifts, purchasing and
settings (readable only to administrators); and database constraints (non-negative stock, positive
quantities) that make whole classes of errors impossible.

# Deployment

**Environments:** `dev` (Docker Compose, hot reload) · `test` (ephemeral database) · `prod`
(Docker/Gunicorn/WhiteNoise/Sentry).

**Production:** the API runs on Render (Gunicorn + WhiteNoise) with a managed PostgreSQL database;
the SPA is deployed to Vercel. Continuous deploy is enabled in `render.yaml`, and on every deploy the
backend runs migrations, seeds the administrator account, collects static files, then starts Gunicorn.
The service is considered healthy once `GET /api/v1/health/` answers, and `deploy/verify_release.py`
compares the live OpenAPI schema against the routes this repository expects, so a stale deployment is
caught before judging:

```bash
python deploy/verify_release.py
```

Migrations and backups:

```bash
docker compose run --rm backend python manage.py makemigrations
docker compose run --rm backend python manage.py migrate
./deploy/backup.sh              # pg_dump
./deploy/restore.sh <file.sql>  # restore
```

# License

Released for the competition submission; contact the author for reuse.

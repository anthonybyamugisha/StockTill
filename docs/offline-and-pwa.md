# Offline-first Selling and PWA

StockTill is a **Progressive Web App (PWA)**: it can be installed on a device
and it keeps working — and keeps selling — when the internet drops.

## Installable app

The frontend ships a web app manifest (`frontend/public/manifest.webmanifest`),
icons, a theme colour and a service worker. In Chrome or Edge, use
**Install app** / **Add to Home screen**. Once installed it opens in its own
window like a native application.

## Service worker caching

`frontend/public/sw.js` caches the application shell and static assets:

- **Navigation requests** are network-first, falling back to the cached
  `index.html`, so the app still loads with no connection.
- **Static assets** (JS, CSS, images) are served cache-first and refreshed in
  the background.
- **API requests are never cached.** Stock levels and prices must be truthful,
  so reads always go to the server; offline writes are handled by the queue
  below.

## Offline selling

A shop's connection can fail mid-sale. When a cashier completes a sale and the
request fails because of a *connection* problem (not a validation error), the
sale is written to a durable queue in `localStorage` and the cashier is told it
has been saved. The sale is not lost.

- `frontend/src/features/pos/offline/saleQueue.ts` stores the sale payload keyed
  by its **idempotency key**.
- `frontend/src/features/pos/offline/saleSync.ts` replays the queue: on app
  start, when the browser fires `online`, and from a manual **Sync now** button.
- A banner across the app shows the offline state and the number of sales
  waiting to sync.

Because every sale carries an idempotency key and the backend de-duplicates on
it, a replay that the server already processed cannot create a duplicate sale.

## What is not queued

Only sales are queued for offline replay. Invoices, refunds, stock adjustments
and administrative actions require a live connection, since they depend on data
other devices may be changing at the same time.

## Tests

- `frontend/src/features/pos/offline/saleQueue.test.ts` — queue, dedupe,
  removal and corrupt-storage recovery.
- `frontend/src/features/pos/offline/saleSync.test.ts` — replay, clear-on-success
  and keep-on-failure behaviour.

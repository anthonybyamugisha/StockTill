# Purchasing and suppliers

The purchasing context tracks who you buy stock from and manages purchase orders
from draft through to receipt. Receiving an order increases stock in the
inventory ledger, so procurement and stock levels stay in step.

## Concepts

- **Supplier** — a vendor you buy from, with contact details.
- **Purchase order (PO)** — a request to a supplier for one or more products at
  agreed unit costs. A PO has a status:
  - `draft` — still being edited at the shop.
  - `ordered` — sent to the supplier.
  - `received` — goods arrived; stock has been added to inventory.
  - `cancelled` — abandoned before receipt.
- **Line** — a product, quantity and unit cost on a PO.

Ordering requires at least one line. Receiving adds each line's quantity to the
product's stock through the inventory context. A received order cannot be
cancelled, and an order can only be received once.

## API

All endpoints require a manager or admin account.

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/api/v1/purchasing/suppliers/` | List suppliers (`?search=` filters by name) |
| POST | `/api/v1/purchasing/suppliers/` | Create a supplier |
| GET  | `/api/v1/purchasing/suppliers/{id}/` | Retrieve a supplier |
| PATCH | `/api/v1/purchasing/suppliers/{id}/` | Update a supplier |
| GET  | `/api/v1/purchasing/orders/` | List purchase orders |
| POST | `/api/v1/purchasing/orders/` | Create a draft purchase order |
| GET  | `/api/v1/purchasing/orders/{id}/` | Retrieve a purchase order |
| POST | `/api/v1/purchasing/orders/{id}/order/` | Mark the order as sent to the supplier |
| POST | `/api/v1/purchasing/orders/{id}/receive/` | Receive the order and add stock |
| POST | `/api/v1/purchasing/orders/{id}/cancel/` | Cancel a draft or ordered PO |

Create a purchase order:

```bash
curl -X POST https://stocktill.onrender.com/api/v1/purchasing/orders/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "supplier_id": "<supplier-id>",
    "reference": "PO-001",
    "lines": [{"product_id": "<product-id>", "quantity": 24, "unit_cost": "2000.00"}]
  }'
```

Then `POST .../orders/<id>/order/` followed by `POST .../orders/<id>/receive/`
to bring the goods into stock.

## Frontend

The **Purchasing** page (sidebar → Purchasing, for managers and admins) has two
tabs:

- **Suppliers** — list, add and edit suppliers.
- **Purchase Orders** — create an order from a supplier (with product, quantity
  and unit cost per line) and move it through *Order → Receive*, or cancel it.
  Receiving refreshes inventory, so low-stock and out-of-stock views update.

## Design notes

- The `purchasing` bounded context owns `Supplier` and `PurchaseOrder`. It never
  writes to the inventory tables directly; receiving calls the inventory context
  through the `StockIntakePort` (implemented by `InventoryStockIntakeAdapter`),
  which records a `purchase` stock movement per line.
- Product names on lines are captured at order time so a PO keeps its history
  even if the catalog entry is later renamed or removed.

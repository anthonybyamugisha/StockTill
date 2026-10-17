# Barcode Scanning

StockTill lets a cashier add products to a sale by barcode in three ways. **No
barcode scanner is required to run or evaluate the system** — a hardware scanner
is optional, and any standard USB or Bluetooth model works out of the box.

## 1. USB / Bluetooth scanner (recommended in a real shop)

Keyboard-wedge (a.k.a. "HID") scanners present themselves to the operating
system as a second keyboard:

1. Buy any USB or Bluetooth barcode scanner (1D laser is enough for retail
   EAN/UPC barcodes; a 2D imager also reads QR codes). Typical price is
   UGX 40,000–150,000.
2. Plug it in (or pair it over Bluetooth). No driver or software is needed.
3. Make sure the scanner is configured to send an **Enter** (CR) suffix after
   the barcode — this is the factory default on almost all models.
4. Open the POS screen; no setup is required in the app.

The POS listens for a fast burst of characters followed by Enter anywhere on the
page, so the cashier can scan without clicking into a field. If the search box
happens to be focused, that field handles the scan instead. Either way the
product is looked up and added to the cart, and a short confirmation banner
appears.

## 2. Camera scanning

Click **Scan with camera** on the POS screen. The browser camera is used to
decode the barcode via the native `BarcodeDetector` API.

| Browser | Support |
|---------|---------|
| Chrome / Edge (desktop and Android) | Yes |
| Safari / Firefox | Not yet — a helpful message is shown |

Camera scanning is a convenience for devices without a dedicated scanner (for
example a phone or tablet). No extra dependency is installed for it.

## 3. Manual entry

Type the barcode into the POS search box and press Enter. Any value of six or
more characters is treated as a barcode and looked up exactly.

## Giving products barcodes

A scan only works if the product has a barcode stored against it. Two options:

- **Use the manufacturer barcode** printed on the product (set it when creating
  or editing the product in the Catalog screen).
- **Generate and print your own labels** for unpackaged goods (for example
  Code128 labels), then scan those.

Barcodes are unique across products, so the same code cannot be assigned twice.

## API

```
GET /api/v1/catalog/products/by-barcode/?barcode=<code>
```

| Status | Meaning |
|--------|---------|
| 200 | Returns the matching active product |
| 400 | The `barcode` query parameter is missing |
| 404 | No active product has that barcode |
| 403 | Not authenticated |

Any authenticated role (including Cashier) may look up a barcode. The POS search
endpoint (`GET /api/v1/catalog/products/?q=<term>`) also matches on name, SKU and
barcode.

## How it works

- `frontend/src/features/pos/lib/barcodeBuffer.ts` — a small, framework-free
  buffer that distinguishes a scanner burst from human typing using the minimum
  length, the average interval between keys, and an idle reset.
- `frontend/src/features/pos/hooks/useBarcodeScanner.ts` — attaches the buffer to
  a page-wide key listener and ignores keystrokes aimed at input fields.
- `frontend/src/features/pos/components/BarcodeCameraModal.tsx` — the camera
  scanner, using `BarcodeDetector` when the browser supports it.

## Tests

- `frontend/src/features/pos/lib/barcodeBuffer.test.ts` covers the scan
  heuristics (fast bursts, human typing, short codes, idle gaps).
- `backend/catalog/tests/api/test_product_barcode.py` covers the lookup endpoint.
- `backend/catalog/tests/api/test_product_search.py` covers name/SKU/barcode
  search.

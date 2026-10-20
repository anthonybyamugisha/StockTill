"""Check that the live backend is serving the current release."""

import json
import sys
import urllib.error
import urllib.request

BASE_URL = "https://stocktill.onrender.com"
REQUIRED_PATHS = (
    "/api/v1/accounts/change-password/",
    "/api/v1/reporting/sales-summary/csv/",
    "/api/v1/reporting/profit/csv/",
    "/api/v1/reporting/inventory/csv/",
    "/api/v1/reporting/top-products/csv/",
    "/api/v1/reporting/cashier-sales/csv/",
    "/api/v1/reporting/low-stock/csv/",
    "/api/v1/reporting/by-payment-method/csv/",
)


def fetch_json(path: str) -> dict:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode())


def main() -> int:
    try:
        schema = fetch_json("/api/schema/")
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"Could not read the live schema: {error}")
        return 1

    paths = schema.get("paths", {})
    missing = [path for path in REQUIRED_PATHS if path not in paths]
    if missing:
        print("The live backend is older than this repository. Missing:")
        for path in missing:
            print(f"  {path}")
        print("Redeploy stocktill-api on Render, then run this check again.")
        return 1

    print("The live backend exposes the current account and reporting routes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

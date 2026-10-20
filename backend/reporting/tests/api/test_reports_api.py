from datetime import UTC, date, datetime

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.domain.entities import Role, User
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from catalog.infrastructure.models import ProductModel
from inventory.infrastructure.models import StockItemModel
from sales.infrastructure.models import PaymentModel, SaleLineModel, SaleModel


def _make_user(email, role):
    user = User(email=email, first_name=role, last_name="User", role=role)
    user.set_password("password123", DjangoPasswordHasher())
    return UserModel.objects.create(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        password=user.password_hash,
        is_active=True,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def manager_user(db):
    return _make_user("manager@shop.com", Role.MANAGER)


@pytest.fixture
def cashier_user(db):
    return _make_user("cashier@shop.com", Role.CASHIER)


@pytest.fixture
def product(db):
    return ProductModel.objects.create(
        name="Sugar 1kg",
        sku="SUG-001",
        buying_cost="1000.00",
        selling_price="1500.00",
        minimum_stock_level=10,
        is_active=True,
    )


@pytest.fixture
def stock_item(db, product):
    return StockItemModel.objects.create(product_id=product.id, quantity_on_hand=5)


@pytest.fixture
def sale(db, product, cashier_user):
    s = SaleModel.objects.create(
        receipt_number="ST-2026-000001",
        cashier_id=cashier_user.id,
        status="completed",
        subtotal="1500.00",
        total_discount="0.00",
        total="1500.00",
    )
    SaleLineModel.objects.create(
        sale=s,
        product_id=product.id,
        product_name=product.name,
        quantity=1,
        unit_price="1500.00",
        unit_cost="1000.00",
    )
    PaymentModel.objects.create(sale=s, method="cash", amount="1500.00")
    return s


@pytest.mark.django_db
def test_dashboard_returns_stats(api_client, manager_user, product, stock_item):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/reporting/dashboard/")
    assert response.status_code == 200
    assert response.data["total_products"] == 1
    assert response.data["low_stock_count"] == 1
    assert response.data["out_of_stock_count"] == 0


@pytest.mark.django_db
def test_inventory_report_valuates_stock(api_client, manager_user, product, stock_item):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/reporting/inventory/")
    assert response.status_code == 200
    assert response.data["total_value"] == "5000.00"
    assert response.data["low_stock_count"] == 1


@pytest.mark.django_db
def test_low_stock_report_lists_item(api_client, manager_user, product, stock_item):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/reporting/low-stock/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["sku"] == "SUG-001"
    assert response.data[0]["minimum_level"] == 10


@pytest.mark.django_db
def test_profit_report_computes_cost_and_profit(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get(
        "/api/v1/reporting/profit/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )
    assert response.status_code == 200
    row = response.data[0]
    assert row["total_revenue"] == "1500.00"
    assert row["total_cost"] == "1000.00"
    assert row["gross_profit"] == "500.00"


@pytest.mark.django_db
def test_top_products_uses_catalog_name_when_line_blank(
    api_client, manager_user, product, cashier_user
):
    s = SaleModel.objects.create(
        receipt_number="ST-2026-000099",
        cashier_id=cashier_user.id,
        status="completed",
        subtotal="1500.00",
        total_discount="0.00",
        total="1500.00",
    )
    SaleLineModel.objects.create(
        sale=s,
        product_id=product.id,
        product_name="",
        quantity=2,
        unit_price="1500.00",
        unit_cost="1000.00",
    )
    api_client.force_authenticate(user=manager_user)
    response = api_client.get(
        "/api/v1/reporting/top-products/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )
    assert response.status_code == 200
    assert response.data[0]["product_name"] == "Sugar 1kg"
    assert response.data[0]["quantity_sold"] == 2


@pytest.mark.django_db
def test_sales_report_includes_cashier_name(api_client, manager_user, cashier_user, sale):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get(
        "/api/v1/reporting/sales-report/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )
    assert response.status_code == 200
    assert response.data[0]["cashier_name"] == "cashier User"


@pytest.mark.django_db
def test_sales_report_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/reporting/sales-report/csv/")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert "ST-2026-000001" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_requires_authentication(api_client):
    response = api_client.get("/api/v1/reporting/dashboard/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_reports_require_manager(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/reporting/sales-summary/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_allowed_for_cashier(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)
    response = api_client.get("/api/v1/reporting/dashboard/")
    assert response.status_code == 200


def _sale_at(receipt_number, cashier_id, created_at):
    sale = SaleModel.objects.create(
        receipt_number=receipt_number,
        cashier_id=cashier_id,
        status="completed",
        subtotal="1500.00",
        total_discount="0.00",
        total="1500.00",
    )
    SaleModel.objects.filter(id=sale.id).update(created_at=created_at)
    return sale


def _buckets(response):
    return {row["date"]: row for row in response.data}


@pytest.mark.django_db
def test_dashboard_today_uses_the_shop_timezone(api_client, manager_user, monkeypatch):
    late_night_utc = datetime(2026, 10, 17, 22, 30, tzinfo=UTC)
    monkeypatch.setattr(timezone, "now", lambda: late_night_utc)
    _sale_at("ST-2026-000042", manager_user.id, late_night_utc)

    assert late_night_utc.date() == date(2026, 10, 17)
    assert timezone.localdate(late_night_utc) == date(2026, 10, 18)

    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/reporting/dashboard/")

    assert response.status_code == 200
    assert response.data["today_revenue"] == "1500.00"


@pytest.mark.django_db
def test_sale_after_midnight_kampala_counts_on_the_new_day(api_client, manager_user, monkeypatch):
    monkeypatch.setattr(
        "reporting.interfaces.api.date_range.timezone.localdate", lambda: date(2026, 10, 18)
    )
    _sale_at("ST-2026-000043", manager_user.id, datetime(2026, 10, 17, 22, 30, tzinfo=UTC))

    api_client.force_authenticate(user=manager_user)
    response = api_client.get("/api/v1/reporting/daily-sales/")

    assert response.status_code == 200
    assert _buckets(response)["2026-10-18"]["transaction_count"] == 1


@pytest.mark.django_db
def test_daily_sales_includes_days_without_sales(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/daily-sales/",
        {"date_from": "2000-01-01", "date_to": "2000-01-03"},
    )

    assert response.status_code == 200
    assert [row["date"] for row in response.data] == ["2000-01-01", "2000-01-02", "2000-01-03"]
    assert _buckets(response)["2000-01-02"] == {
        "date": "2000-01-02",
        "transaction_count": 0,
        "total": "0.00",
    }


@pytest.mark.django_db
def test_profit_report_groups_sales_on_the_shop_day(api_client, manager_user, sale):
    SaleModel.objects.filter(id=sale.id).update(
        created_at=datetime(2026, 10, 17, 21, 30, tzinfo=UTC)
    )
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/profit/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert [row["date"] for row in response.data] == ["2026-10-18"]


@pytest.mark.django_db
def test_sales_summary_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/sales-summary/csv/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == "attachment; filename=sales_summary.csv"
    body = response.content.decode()
    assert body.startswith("From,To,Total Sales,Revenue,Cost,Gross Profit,Average Sale")
    assert "2000-01-01,2100-01-01,1,1500.00,1000.00,500.00,1500.00" in body


@pytest.mark.django_db
def test_daily_sales_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/daily-sales/csv/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=daily_sales.csv"
    body = response.content.decode()
    assert body.startswith("Date,Transactions,Total")
    assert "1,1500.00" in body


@pytest.mark.django_db
def test_profit_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/profit/csv/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=profit_report.csv"
    body = response.content.decode()
    assert body.startswith("Date,Revenue,Cost,Gross Profit")
    assert "1500.00,1000.00,500.00" in body


@pytest.mark.django_db
def test_top_products_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/top-products/csv/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=top_products.csv"
    body = response.content.decode()
    assert body.startswith("Product,Qty Sold,Revenue")
    assert "Sugar 1kg,1,1500.00" in body


@pytest.mark.django_db
def test_cashier_sales_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/cashier-sales/csv/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=cashier_sales.csv"
    body = response.content.decode()
    assert body.startswith("Cashier,Transactions,Total")
    assert "cashier User,1,1500.00" in body


@pytest.mark.django_db
def test_low_stock_csv_export(api_client, manager_user, product, stock_item):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/reporting/low-stock/csv/")

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=low_stock.csv"
    body = response.content.decode()
    assert body.startswith("Product,SKU,Qty On Hand,Minimum Level")
    assert "Sugar 1kg,SUG-001,5,10" in body


@pytest.mark.django_db
def test_inventory_csv_export(api_client, manager_user, product, stock_item):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get("/api/v1/reporting/inventory/csv/")

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=inventory_report.csv"
    body = response.content.decode()
    assert body.startswith("Total Products,Inventory Value,Low Stock,Out of Stock")
    assert "1,5000.00,1,0" in body


@pytest.mark.django_db
def test_payment_method_csv_export(api_client, manager_user, sale):
    api_client.force_authenticate(user=manager_user)

    response = api_client.get(
        "/api/v1/reporting/by-payment-method/csv/",
        {"date_from": "2000-01-01", "date_to": "2100-01-01"},
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=sales_by_payment_method.csv"
    body = response.content.decode()
    assert body.startswith("Payment Method,Transactions,Total")
    assert "cash,1,1500.00" in body


@pytest.mark.django_db
def test_csv_exports_require_manager(api_client, cashier_user):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.get("/api/v1/reporting/profit/csv/")

    assert response.status_code == 403

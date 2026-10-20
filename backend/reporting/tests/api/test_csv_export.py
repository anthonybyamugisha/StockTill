from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from reporting.application.queries import (
    CashierSales,
    DailySales,
    InventoryReport,
    LowStockItem,
    ProfitReport,
    SalesByPaymentMethod,
    SalesReportRow,
    SalesSummary,
    TopProduct,
)
from reporting.interfaces.api.csv_export import (
    write_cashier_sales_csv,
    write_daily_sales_csv,
    write_inventory_report_csv,
    write_low_stock_csv,
    write_payment_methods_csv,
    write_profit_report_csv,
    write_sales_report_csv,
    write_sales_summary_csv,
    write_top_products_csv,
)


def _row(cashier_name: str = "Grace Nakato") -> SalesReportRow:
    return SalesReportRow(
        receipt_number="ST-2026-000001",
        date=datetime(2026, 10, 18, 0, 42),
        cashier_name=cashier_name,
        total=Decimal("4500.00"),
        payment_method="cash",
        status="completed",
    )


def test_writes_a_header_and_one_line_per_row():
    lines = write_sales_report_csv([_row()]).splitlines()

    assert lines[0] == "Receipt,Date,Cashier,Total,Payment Method,Status"
    assert lines[1] == "ST-2026-000001,2026-10-18T00:42:00,Grace Nakato,4500.00,cash,completed"


def test_quotes_values_that_contain_a_comma():
    lines = write_sales_report_csv([_row(cashier_name="Nakato, Grace")]).splitlines()

    assert lines[1].startswith('ST-2026-000001,2026-10-18T00:42:00,"Nakato, Grace",')


def test_writes_only_the_header_for_an_empty_report():
    assert write_sales_report_csv([]).splitlines() == [
        "Receipt,Date,Cashier,Total,Payment Method,Status"
    ]


def _summary() -> SalesSummary:
    return SalesSummary(
        total_sales=3,
        total_revenue=Decimal("4500.00"),
        total_cost=Decimal("3000.00"),
        gross_profit=Decimal("1500.00"),
        average_sale_value=Decimal("1500.00"),
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 18),
    )


def test_writes_the_sales_summary_as_a_single_row():
    lines = write_sales_summary_csv(_summary()).splitlines()

    assert lines[0] == "From,To,Total Sales,Revenue,Cost,Gross Profit,Average Sale"
    assert lines[1] == "2026-10-01,2026-10-18,3,4500.00,3000.00,1500.00,1500.00"


def test_writes_daily_sales_with_one_line_per_day():
    rows = [
        DailySales(date=date(2026, 10, 17), transaction_count=2, total=Decimal("3000.00")),
        DailySales(date=date(2026, 10, 18), transaction_count=0, total=Decimal("0.00")),
    ]

    lines = write_daily_sales_csv(rows).splitlines()

    assert lines[0] == "Date,Transactions,Total"
    assert lines[1] == "2026-10-17,2,3000.00"
    assert lines[2] == "2026-10-18,0,0.00"


def test_writes_profit_by_day():
    rows = [
        ProfitReport(
            date=date(2026, 10, 18),
            total_revenue=Decimal("1500.00"),
            total_cost=Decimal("1000.00"),
            gross_profit=Decimal("500.00"),
        )
    ]

    lines = write_profit_report_csv(rows).splitlines()

    assert lines[0] == "Date,Revenue,Cost,Gross Profit"
    assert lines[1] == "2026-10-18,1500.00,1000.00,500.00"


def test_writes_top_products():
    rows = [
        TopProduct(
            product_id=UUID("00000000-0000-0000-0000-000000000001"),
            product_name="Sugar 1kg",
            quantity_sold=2,
            revenue=Decimal("3000.00"),
        )
    ]

    lines = write_top_products_csv(rows).splitlines()

    assert lines[0] == "Product,Qty Sold,Revenue"
    assert lines[1] == "Sugar 1kg,2,3000.00"


def test_writes_sales_by_cashier():
    rows = [
        CashierSales(
            cashier_id=UUID("00000000-0000-0000-0000-000000000002"),
            cashier_name="Grace Nakato",
            transaction_count=4,
            total=Decimal("6000.00"),
        )
    ]

    lines = write_cashier_sales_csv(rows).splitlines()

    assert lines[0] == "Cashier,Transactions,Total"
    assert lines[1] == "Grace Nakato,4,6000.00"


def test_writes_low_stock_items():
    rows = [
        LowStockItem(
            product_id=UUID("00000000-0000-0000-0000-000000000003"),
            product_name="Sugar 1kg",
            sku="SUG-001",
            quantity_on_hand=5,
            minimum_level=10,
        )
    ]

    lines = write_low_stock_csv(rows).splitlines()

    assert lines[0] == "Product,SKU,Qty On Hand,Minimum Level"
    assert lines[1] == "Sugar 1kg,SUG-001,5,10"


def test_writes_the_inventory_summary():
    report = InventoryReport(
        total_products=12,
        total_value=Decimal("45000.00"),
        low_stock_count=2,
        out_of_stock_count=1,
    )

    lines = write_inventory_report_csv(report).splitlines()

    assert lines[0] == "Total Products,Inventory Value,Low Stock,Out of Stock"
    assert lines[1] == "12,45000.00,2,1"


def test_writes_sales_by_payment_method():
    rows = [
        SalesByPaymentMethod(method="cash", count=3, total=Decimal("4500.00")),
        SalesByPaymentMethod(method="mobile_money", count=2, total=Decimal("3000.00")),
    ]

    lines = write_payment_methods_csv(rows).splitlines()

    assert lines[0] == "Payment Method,Transactions,Total"
    assert lines[1] == "cash,3,4500.00"
    assert lines[2] == "mobile_money,2,3000.00"

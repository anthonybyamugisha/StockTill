from datetime import date, datetime
from decimal import Decimal

from reporting.application.queries import SalesReportRow, SalesSummary
from reporting.interfaces.api.csv_export import write_sales_report_csv, write_sales_summary_csv


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

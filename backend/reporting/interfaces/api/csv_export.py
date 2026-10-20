import csv
from io import StringIO

from reporting.application.queries import SalesReportRow, SalesSummary

SALES_REPORT_HEADER = ["Receipt", "Date", "Cashier", "Total", "Payment Method", "Status"]


def _write_rows(header: list[str], rows: list[list[str]]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()


def _money(value: object) -> str:
    return f"{value:.2f}"


def write_sales_report_csv(rows: list[SalesReportRow]) -> str:
    return _write_rows(
        SALES_REPORT_HEADER,
        [
            [
                row.receipt_number,
                row.date.isoformat(),
                row.cashier_name,
                _money(row.total),
                row.payment_method,
                row.status,
            ]
            for row in rows
        ],
    )


def write_sales_summary_csv(summary: SalesSummary) -> str:
    return _write_rows(
        ["From", "To", "Total Sales", "Revenue", "Cost", "Gross Profit", "Average Sale"],
        [
            [
                summary.date_from.isoformat(),
                summary.date_to.isoformat(),
                str(summary.total_sales),
                _money(summary.total_revenue),
                _money(summary.total_cost),
                _money(summary.gross_profit),
                _money(summary.average_sale_value),
            ]
        ],
    )
import csv
from io import StringIO

from reporting.application.queries import SalesReportRow

SALES_REPORT_HEADER = ["Receipt", "Date", "Cashier", "Total", "Payment Method", "Status"]


def write_sales_report_csv(rows: list[SalesReportRow]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(SALES_REPORT_HEADER)
    for row in rows:
        writer.writerow(
            [
                row.receipt_number,
                row.date.isoformat(),
                row.cashier_name,
                str(row.total),
                row.payment_method,
                row.status,
            ]
        )
    return output.getvalue()

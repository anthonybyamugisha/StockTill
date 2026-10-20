import csv
from io import StringIO

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


def write_daily_sales_csv(rows: list[DailySales]) -> str:
    return _write_rows(
        ["Date", "Transactions", "Total"],
        [[row.date.isoformat(), str(row.transaction_count), _money(row.total)] for row in rows],
    )


def write_profit_report_csv(rows: list[ProfitReport]) -> str:
    return _write_rows(
        ["Date", "Revenue", "Cost", "Gross Profit"],
        [
            [
                row.date.isoformat(),
                _money(row.total_revenue),
                _money(row.total_cost),
                _money(row.gross_profit),
            ]
            for row in rows
        ],
    )


def write_top_products_csv(rows: list[TopProduct]) -> str:
    return _write_rows(
        ["Product", "Qty Sold", "Revenue"],
        [[row.product_name, str(row.quantity_sold), _money(row.revenue)] for row in rows],
    )


def write_cashier_sales_csv(rows: list[CashierSales]) -> str:
    return _write_rows(
        ["Cashier", "Transactions", "Total"],
        [[row.cashier_name, str(row.transaction_count), _money(row.total)] for row in rows],
    )


def write_low_stock_csv(rows: list[LowStockItem]) -> str:
    return _write_rows(
        ["Product", "SKU", "Qty On Hand", "Minimum Level"],
        [
            [
                row.product_name,
                row.sku,
                str(row.quantity_on_hand),
                str(row.minimum_level),
            ]
            for row in rows
        ],
    )


def write_inventory_report_csv(report: InventoryReport) -> str:
    return _write_rows(
        ["Total Products", "Inventory Value", "Low Stock", "Out of Stock"],
        [
            [
                str(report.total_products),
                _money(report.total_value),
                str(report.low_stock_count),
                str(report.out_of_stock_count),
            ]
        ],
    )


def write_payment_methods_csv(rows: list[SalesByPaymentMethod]) -> str:
    return _write_rows(
        ["Payment Method", "Transactions", "Total"],
        [[row.method, str(row.count), _money(row.total)] for row in rows],
    )

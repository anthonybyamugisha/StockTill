from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class SalesSummary:
    total_sales: int
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    average_sale_value: Decimal
    date_from: date
    date_to: date


@dataclass(frozen=True)
class TopProduct:
    product_id: UUID
    product_name: str
    quantity_sold: int
    revenue: Decimal


@dataclass(frozen=True)
class SalesByPaymentMethod:
    method: str
    count: int
    total: Decimal


@dataclass(frozen=True)
class DailySales:
    date: date
    transaction_count: int
    total: Decimal


@dataclass(frozen=True)
class CashierSales:
    cashier_id: UUID
    cashier_name: str
    transaction_count: int
    total: Decimal


@dataclass(frozen=True)
class DashboardStats:
    today_sales: int
    today_revenue: Decimal
    week_sales: int
    week_revenue: Decimal
    month_sales: int
    month_revenue: Decimal
    total_transactions: int
    total_products: int
    low_stock_count: int
    out_of_stock_count: int
    average_sale_value: Decimal
    gross_profit: Decimal


@dataclass(frozen=True)
class ProfitReport:
    date: date
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal


@dataclass(frozen=True)
class InventoryReport:
    total_products: int
    total_value: Decimal
    low_stock_count: int
    out_of_stock_count: int


@dataclass(frozen=True)
class SalesReportRow:
    receipt_number: str
    date: datetime
    cashier_name: str
    total: Decimal
    payment_method: str
    status: str


@dataclass(frozen=True)
class LowStockItem:
    product_id: UUID
    product_name: str
    sku: str
    quantity_on_hand: int
    minimum_level: int

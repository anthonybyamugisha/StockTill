from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from shared.domain.money import Money


@dataclass(frozen=True)
class SalesSummary:
    total_sales: int
    total_revenue: Money
    total_cost: Money
    gross_profit: Money
    average_sale_value: Money
    date_from: date
    date_to: date


@dataclass(frozen=True)
class TopProduct:
    product_id: str
    product_name: str
    quantity_sold: int
    revenue: Money


@dataclass(frozen=True)
class SalesByPaymentMethod:
    method: str
    count: int
    total: Money


@dataclass(frozen=True)
class DailySales:
    date: date
    transaction_count: int
    total: Money


@dataclass(frozen=True)
class CashierSales:
    cashier_id: str
    cashier_name: str
    transaction_count: int
    total: Money

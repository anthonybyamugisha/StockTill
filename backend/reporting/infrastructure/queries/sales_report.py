from datetime import date

from reporting.application.queries import SalesReportRow
from reporting.infrastructure.directories import CashierDirectory
from sales.infrastructure.models import SaleModel


class DjangoSalesReportQuery:
    def execute(self, date_from: date, date_to: date) -> list[SalesReportRow]:
        cashiers = CashierDirectory.load()
        sales = SaleModel.objects.filter(created_at__date__range=(date_from, date_to)).order_by(
            "-created_at"
        )
        rows = []
        for sale in sales:
            for payment in sale.payments.all():
                rows.append(
                    SalesReportRow(
                        receipt_number=sale.receipt_number,
                        date=sale.created_at,
                        cashier_name=cashiers.label_for(sale.cashier_id),
                        total=sale.total,
                        payment_method=payment.method,
                        status=sale.status,
                    )
                )
        return rows

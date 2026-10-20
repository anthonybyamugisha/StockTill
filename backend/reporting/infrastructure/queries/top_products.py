from datetime import date

from django.db.models import F, Sum

from catalog.infrastructure.models import ProductModel
from reporting.application.queries import TopProduct
from sales.infrastructure.models import SaleLineModel


class DjangoTopProductsQuery:
    def execute(self, date_from: date, date_to: date, limit: int = 10) -> list[TopProduct]:
        rows = list(
            SaleLineModel.objects.filter(sale__created_at__date__range=(date_from, date_to))
            .values("product_id")
            .annotate(total_qty=Sum("quantity"), total_rev=Sum(F("quantity") * F("unit_price")))
            .order_by("-total_qty")[:limit]
        )
        product_ids = [row["product_id"] for row in rows]
        catalog_names = dict(
            ProductModel.objects.filter(id__in=product_ids).values_list("id", "name")
        )
        line_names: dict = {}
        for product_id, line_name in SaleLineModel.objects.filter(
            product_id__in=product_ids
        ).values_list("product_id", "product_name"):
            if line_name:
                line_names.setdefault(product_id, line_name)
        return [
            TopProduct(
                product_id=row["product_id"],
                product_name=catalog_names.get(row["product_id"])
                or line_names.get(row["product_id"])
                or "Unknown product",
                quantity_sold=row["total_qty"],
                revenue=row["total_rev"],
            )
            for row in rows
        ]

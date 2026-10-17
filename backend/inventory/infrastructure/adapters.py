from uuid import UUID

from inventory.application.ports import ProductInfoPort


class CatalogProductInfoAdapter(ProductInfoPort):
    def get_product_name(self, product_id: UUID) -> str | None:
        from catalog.infrastructure.models import ProductModel

        try:
            return ProductModel.objects.get(id=product_id).name
        except ProductModel.DoesNotExist:
            return None

    def get_minimum_stock_level(self, product_id: UUID) -> int:
        from catalog.infrastructure.models import ProductModel

        try:
            return ProductModel.objects.get(id=product_id).minimum_stock_level
        except ProductModel.DoesNotExist:
            return 0

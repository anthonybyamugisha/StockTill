from uuid import UUID

from catalog.domain.entities import Category, Product
from catalog.domain.repository import CategoryRepository, ProductRepository
from catalog.infrastructure.models import CategoryModel, ProductModel
from shared.domain.money import Money


class DjangoProductRepository(ProductRepository):
    def get_by_id(self, product_id: UUID) -> Product | None:
        try:
            m = ProductModel.objects.get(id=product_id)
            return self._to_domain(m)
        except ProductModel.DoesNotExist:
            return None

    def get_by_sku(self, sku: str) -> Product | None:
        try:
            m = ProductModel.objects.get(sku=sku)
            return self._to_domain(m)
        except ProductModel.DoesNotExist:
            return None

    def get_by_barcode(self, barcode: str) -> Product | None:
        try:
            m = ProductModel.objects.get(barcode=barcode)
            return self._to_domain(m)
        except ProductModel.DoesNotExist:
            return None

    def search(self, query: str, *, active_only: bool = True) -> list[Product]:
        qs = ProductModel.objects.filter(name__icontains=query)
        if active_only:
            qs = qs.filter(is_active=True)
        return [self._to_domain(m) for m in qs]

    def list_products(self, *, active_only: bool = True) -> list[Product]:
        qs = ProductModel.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return [self._to_domain(m) for m in qs]

    def save(self, product: Product) -> None:
        ProductModel.objects.update_or_create(
            id=product.id,
            defaults={
                "name": product.name,
                "description": product.description,
                "sku": product.sku,
                "barcode": product.barcode,
                "category_id": product.category_id,
                "buying_cost": product.buying_cost.amount,
                "selling_price": product.selling_price.amount,
                "minimum_stock_level": product.minimum_stock_level,
                "image_url": product.image_url,
                "is_active": product.is_active,
            },
        )

    def _to_domain(self, m: ProductModel) -> Product:
        return Product(
            id=m.id,
            name=m.name,
            description=m.description,
            sku=m.sku,
            barcode=m.barcode,
            category_id=m.category_id,
            buying_cost=Money(m.buying_cost),
            selling_price=Money(m.selling_price),
            minimum_stock_level=m.minimum_stock_level,
            image_url=m.image_url,
            is_active=m.is_active,
        )


class DjangoCategoryRepository(CategoryRepository):
    def get_by_id(self, category_id: UUID) -> Category | None:
        try:
            m = CategoryModel.objects.get(id=category_id)
            return Category(id=m.id, name=m.name, description=m.description)
        except CategoryModel.DoesNotExist:
            return None

    def list_categories(self) -> list[Category]:
        return [
            Category(id=m.id, name=m.name, description=m.description)
            for m in CategoryModel.objects.all()
        ]

    def save(self, category: Category) -> None:
        CategoryModel.objects.update_or_create(
            id=category.id,
            defaults={"name": category.name, "description": category.description},
        )

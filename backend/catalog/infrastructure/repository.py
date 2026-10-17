from uuid import UUID

from django.db.models import Q

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
            m = ProductModel.objects.get(sku__iexact=sku)
            return self._to_domain(m)
        except ProductModel.DoesNotExist:
            return None

    def get_by_barcode(self, barcode: str) -> Product | None:
        try:
            m = ProductModel.objects.get(barcode=barcode)
            return self._to_domain(m)
        except ProductModel.DoesNotExist:
            return None

    def search(
        self,
        query: str,
        *,
        active_only: bool = True,
        category_id: UUID | None = None,
    ) -> list[Product]:
        qs = ProductModel.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query)
        )
        if active_only:
            qs = qs.filter(is_active=True)
        if category_id:
            qs = qs.filter(category_id=category_id)
        return [self._to_domain(m) for m in qs]

    def list_products(
        self,
        *,
        active_only: bool = True,
        category_id: UUID | None = None,
    ) -> list[Product]:
        qs = ProductModel.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        if category_id:
            qs = qs.filter(category_id=category_id)
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

    def sku_exists(self, sku: str, exclude_id: UUID | None = None) -> bool:
        qs = ProductModel.objects.filter(sku__iexact=sku)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def barcode_exists(self, barcode: str, exclude_id: UUID | None = None) -> bool:
        qs = ProductModel.objects.filter(barcode=barcode)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

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
            return Category(
                id=m.id,
                name=m.name,
                description=m.description,
                parent_id=m.parent_id,
                is_active=m.is_active,
            )
        except CategoryModel.DoesNotExist:
            return None

    def list_categories(self, *, active_only: bool = True) -> list[Category]:
        qs = CategoryModel.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return [
            Category(
                id=m.id,
                name=m.name,
                description=m.description,
                parent_id=m.parent_id,
                is_active=m.is_active,
            )
            for m in qs
        ]

    def save(self, category: Category) -> None:
        CategoryModel.objects.update_or_create(
            id=category.id,
            defaults={
                "name": category.name,
                "description": category.description,
                "parent_id": category.parent_id,
                "is_active": category.is_active,
            },
        )

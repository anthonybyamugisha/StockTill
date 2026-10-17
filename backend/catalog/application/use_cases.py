from typing import Any

from catalog.application.commands import (
    CreateCategoryCommand,
    CreateProductCommand,
    DeactivateCategoryCommand,
    DeactivateProductCommand,
    UpdateProductCommand,
)
from catalog.application.ports import OpeningStockPort
from catalog.domain.entities import Category, Product
from catalog.domain.repository import CategoryRepository, ProductRepository
from shared.application.audit import AuditPort, NullAuditPort
from shared.domain.clock import Clock


def _product_snapshot(product: Product) -> dict[str, Any]:
    return {
        "name": product.name,
        "sku": product.sku,
        "barcode": product.barcode,
        "category_id": str(product.category_id) if product.category_id else None,
        "buying_cost": str(product.buying_cost.amount),
        "selling_price": str(product.selling_price.amount),
        "minimum_stock_level": product.minimum_stock_level,
        "is_active": product.is_active,
    }


class CreateProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        clock: Clock,
        opening_stock_port: OpeningStockPort | None = None,
        audit: AuditPort | None = None,
    ):
        self._repo = product_repository
        self._clock = clock
        self._opening_stock = opening_stock_port
        self._audit = audit or NullAuditPort()

    def execute(self, command: CreateProductCommand) -> Product:
        if self._repo.sku_exists(command.sku):
            raise ValueError(f"SKU '{command.sku}' already exists")
        if command.barcode and self._repo.barcode_exists(command.barcode):
            raise ValueError(f"Barcode '{command.barcode}' already exists")

        product = Product(
            name=command.name,
            description=command.description,
            sku=command.sku,
            barcode=command.barcode,
            category_id=command.category_id,
            buying_cost=command.buying_cost,
            selling_price=command.selling_price,
            minimum_stock_level=command.minimum_stock_level,
            image_url=command.image_url,
        )
        self._repo.save(product)

        if command.opening_stock > 0 and self._opening_stock is not None:
            self._opening_stock.record_opening_stock(
                product_id=product.id,
                quantity=command.opening_stock,
                unit_cost=command.buying_cost,
                user_id=command.user_id,
            )

        after = _product_snapshot(product)
        after["opening_stock"] = command.opening_stock
        self._audit.record(
            user_id=command.user_id,
            action="product.created",
            entity_type="product",
            entity_id=str(product.id),
            after=after,
        )
        return product


class UpdateProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._repo = product_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: UpdateProductCommand) -> Product:
        product = self._repo.get_by_id(command.product_id)
        if product is None:
            raise ValueError("Product not found")

        before = _product_snapshot(product)

        if command.sku is not None and command.sku != product.sku:
            if self._repo.sku_exists(command.sku, exclude_id=product.id):
                raise ValueError(f"SKU '{command.sku}' already exists")
            product.sku = command.sku

        if command.barcode and command.barcode != product.barcode:
            if self._repo.barcode_exists(command.barcode, exclude_id=product.id):
                raise ValueError(f"Barcode '{command.barcode}' already exists")
            product.barcode = command.barcode

        if command.name is not None:
            product.name = command.name
        if command.description is not None:
            product.description = command.description
        if command.category_id is not None:
            product.category_id = command.category_id
        if command.minimum_stock_level is not None:
            product.minimum_stock_level = command.minimum_stock_level
        if command.image_url is not None:
            product.image_url = command.image_url
        if command.is_active is not None:
            product.is_active = command.is_active

        if command.selling_price is not None and command.selling_price != product.selling_price:
            product.update_price(command.selling_price, command.user_id or product.id)
        if command.buying_cost is not None and command.buying_cost != product.buying_cost:
            product.update_cost(command.buying_cost, command.user_id or product.id)

        self._repo.save(product)

        after = _product_snapshot(product)
        changed = {key: value for key, value in after.items() if value != before[key]}
        if changed:
            self._audit.record(
                user_id=command.user_id,
                action="product.updated",
                entity_type="product",
                entity_id=str(product.id),
                before={key: before[key] for key in changed},
                after=changed,
            )
        return product


class DeactivateProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepository,
        clock: Clock,
        audit: AuditPort | None = None,
    ):
        self._repo = product_repository
        self._clock = clock
        self._audit = audit or NullAuditPort()

    def execute(self, command: DeactivateProductCommand) -> Product:
        product = self._repo.get_by_id(command.product_id)
        if product is None:
            raise ValueError("Product not found")

        product.is_active = False
        self._repo.save(product)
        self._audit.record(
            user_id=command.user_id,
            action="product.deactivated",
            entity_type="product",
            entity_id=str(product.id),
            before={"is_active": True},
            after={"is_active": False, "name": product.name, "sku": product.sku},
        )
        return product


class CreateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository, audit: AuditPort | None = None):
        self._repo = category_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: CreateCategoryCommand) -> Category:
        category = Category(
            name=command.name,
            description=command.description,
            parent_id=command.parent_id,
        )
        self._repo.save(category)
        self._audit.record(
            user_id=command.user_id,
            action="category.created",
            entity_type="category",
            entity_id=str(category.id),
            after={"name": category.name},
        )
        return category


class ListCategoriesUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self._repo = category_repository

    def execute(self, active_only: bool = True) -> list[Category]:
        return self._repo.list_categories(active_only=active_only)


class DeactivateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository, audit: AuditPort | None = None):
        self._repo = category_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: DeactivateCategoryCommand) -> Category:
        category = self._repo.get_by_id(command.category_id)
        if category is None:
            raise ValueError("Category not found")

        category.is_active = False
        self._repo.save(category)
        self._audit.record(
            user_id=command.user_id,
            action="category.deactivated",
            entity_type="category",
            entity_id=str(category.id),
            before={"is_active": True, "name": category.name},
            after={"is_active": False},
        )
        return category

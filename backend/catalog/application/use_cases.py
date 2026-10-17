from catalog.application.commands import (
    CreateCategoryCommand,
    CreateProductCommand,
    DeactivateProductCommand,
    UpdateProductCommand,
)
from catalog.domain.entities import Category, Product
from catalog.domain.events import PriceChanged, ProductDeactivated
from catalog.domain.repository import CategoryRepository, ProductRepository
from shared.domain.clock import Clock


class CreateProductUseCase:
    def __init__(self, product_repository: ProductRepository, clock: Clock):
        self._repo = product_repository
        self._clock = clock

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
        return product


class UpdateProductUseCase:
    def __init__(self, product_repository: ProductRepository, clock: Clock):
        self._repo = product_repository
        self._clock = clock

    def execute(self, command: UpdateProductCommand) -> Product:
        product = self._repo.get_by_id(command.product_id)
        if product is None:
            raise ValueError("Product not found")

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
        return product


class DeactivateProductUseCase:
    def __init__(self, product_repository: ProductRepository, clock: Clock):
        self._repo = product_repository
        self._clock = clock

    def execute(self, command: DeactivateProductCommand) -> Product:
        product = self._repo.get_by_id(command.product_id)
        if product is None:
            raise ValueError("Product not found")

        product.is_active = False
        self._repo.save(product)
        return product


class CreateCategoryUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self._repo = category_repository

    def execute(self, command: CreateCategoryCommand) -> Category:
        category = Category(
            name=command.name,
            description=command.description,
            parent_id=command.parent_id,
        )
        self._repo.save(category)
        return category


class ListCategoriesUseCase:
    def __init__(self, category_repository: CategoryRepository):
        self._repo = category_repository

    def execute(self, active_only: bool = True) -> list[Category]:
        return self._repo.list_categories(active_only=active_only)

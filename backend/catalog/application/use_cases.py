from catalog.application.commands import (
    CreateProductCommand,
    DeactivateProductCommand,
    UpdateProductCommand,
)
from catalog.domain.entities import Product
from catalog.domain.repository import ProductRepository


class CreateProductUseCase:
    def __init__(self, product_repository: ProductRepository):
        self._repo = product_repository

    def execute(self, command: CreateProductCommand) -> Product:
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
    def __init__(self, product_repository: ProductRepository):
        self._repo = product_repository

    def execute(self, command: UpdateProductCommand) -> Product:
        product = self._repo.get_by_id(command.product_id)
        if product is None:
            raise ValueError("Product not found")
        if command.name is not None:
            product.name = command.name
        if command.description is not None:
            product.description = command.description
        if command.barcode is not None:
            product.barcode = command.barcode
        if command.category_id is not None:
            product.category_id = command.category_id
        if command.buying_cost is not None:
            product.buying_cost = command.buying_cost
        if command.selling_price is not None:
            product.selling_price = command.selling_price
        if command.minimum_stock_level is not None:
            product.minimum_stock_level = command.minimum_stock_level
        if command.image_url is not None:
            product.image_url = command.image_url
        self._repo.save(product)
        return product


class DeactivateProductUseCase:
    def __init__(self, product_repository: ProductRepository):
        self._repo = product_repository

    def execute(self, command: DeactivateProductCommand) -> Product:
        product = self._repo.get_by_id(command.product_id)
        if product is None:
            raise ValueError("Product not found")
        product.is_active = False
        self._repo.save(product)
        return product

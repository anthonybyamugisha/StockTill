from decimal import Decimal
from uuid import UUID

from inventory.domain.entities import MovementType, StockItem, StockMovement
from inventory.domain.repository import StockItemRepository, StockMovementRepository
from inventory.infrastructure.models import StockItemModel, StockMovementModel
from shared.domain.money import Money


class DjangoStockMovementRepository(StockMovementRepository):
    def save(self, movement: StockMovement) -> None:
        StockMovementModel.objects.create(
            id=movement.id,
            product_id=movement.product_id,
            quantity=movement.quantity,
            movement_type=movement.movement_type.value,
            reason=movement.reason,
            reference=movement.reference,
            unit_cost=movement.unit_cost.amount,
            user_id=movement.user_id,
            notes=movement.notes,
        )

    def get_by_id(self, movement_id: UUID) -> StockMovement | None:
        try:
            m = StockMovementModel.objects.get(id=movement_id)
            return self._to_domain(m)
        except StockMovementModel.DoesNotExist:
            return None

    def list_by_product(self, product_id: UUID) -> list[StockMovement]:
        return [
            self._to_domain(m)
            for m in StockMovementModel.objects.filter(product_id=product_id).order_by("-timestamp")
        ]

    def list_all(
        self,
        *,
        movement_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[StockMovement]:
        qs = StockMovementModel.objects.all()
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
        return [self._to_domain(m) for m in qs]

    def _to_domain(self, m: StockMovementModel) -> StockMovement:
        return StockMovement(
            id=m.id,
            product_id=m.product_id,
            quantity=m.quantity,
            movement_type=MovementType(m.movement_type),
            reason=m.reason,
            reference=m.reference,
            unit_cost=Money(m.unit_cost),
            user_id=m.user_id,
            timestamp=m.timestamp,
            notes=m.notes,
        )


class DjangoStockItemRepository(StockItemRepository):
    def get_by_product(self, product_id: UUID) -> StockItem | None:
        try:
            m = StockItemModel.objects.get(product_id=product_id)
            return StockItem(
                id=m.id,
                product_id=m.product_id,
                quantity_on_hand=m.quantity_on_hand,
                reserved_quantity=m.reserved_quantity,
                last_movement_id=m.last_movement_id,
            )
        except StockItemModel.DoesNotExist:
            return None

    def save(self, item: StockItem) -> None:
        StockItemModel.objects.update_or_create(
            product_id=item.product_id,
            defaults={
                "quantity_on_hand": item.quantity_on_hand,
                "reserved_quantity": item.reserved_quantity,
                "last_movement_id": item.last_movement_id,
            },
        )

    def list_all(self) -> list[StockItem]:
        return [
            StockItem(
                id=m.id,
                product_id=m.product_id,
                quantity_on_hand=m.quantity_on_hand,
                reserved_quantity=m.reserved_quantity,
                last_movement_id=m.last_movement_id,
            )
            for m in StockItemModel.objects.all()
        ]

    def list_low_stock(self) -> list[StockItem]:
        from catalog.infrastructure.models import ProductModel

        items = {m.product_id: m for m in StockItemModel.objects.all()}
        result = []
        for product in ProductModel.objects.filter(is_active=True, minimum_stock_level__gt=0):
            item = items.get(product.id)
            quantity = item.quantity_on_hand if item else 0
            if quantity <= product.minimum_stock_level:
                result.append(
                    StockItem(
                        id=item.id if item else UUID(int=0),
                        product_id=product.id,
                        quantity_on_hand=quantity,
                        reserved_quantity=item.reserved_quantity if item else 0,
                    )
                )
        return result

    def list_out_of_stock(self) -> list[StockItem]:
        from catalog.infrastructure.models import ProductModel

        items = {m.product_id: m for m in StockItemModel.objects.all()}
        result = []
        for product in ProductModel.objects.filter(is_active=True):
            item = items.get(product.id)
            if item is None or item.quantity_on_hand == 0:
                result.append(
                    StockItem(
                        id=item.id if item else UUID(int=0),
                        product_id=product.id,
                        quantity_on_hand=0,
                        reserved_quantity=item.reserved_quantity if item else 0,
                    )
                )
        return result

    def get_valuation(self) -> dict[str, object]:
        from catalog.infrastructure.models import ProductModel

        products = {p.id: p for p in ProductModel.objects.all()}
        total = Money.zero()
        by_product = []
        for item in StockItemModel.objects.all():
            product = products.get(item.product_id)
            if product is None:
                continue
            value = Money(product.buying_cost).multiply(Decimal(item.quantity_on_hand))
            total = total.add(value)
            by_product.append(
                {
                    "product_id": str(item.product_id),
                    "product_name": product.name,
                    "quantity": item.quantity_on_hand,
                    "unit_cost": str(product.buying_cost),
                    "value": str(value.amount),
                }
            )
        return {"total": str(total.amount), "by_product": by_product}

from dataclasses import dataclass
from uuid import UUID

from accounts.infrastructure.models import UserModel
from catalog.infrastructure.models import ProductModel


@dataclass(frozen=True)
class CashierDirectory:
    labels: dict[UUID, str]

    @classmethod
    def load(cls) -> "CashierDirectory":
        return cls(
            {
                user.id: f"{user.first_name} {user.last_name}".strip() or user.email
                for user in UserModel.objects.all()
            }
        )

    def label_for(self, cashier_id: UUID) -> str:
        return self.labels.get(cashier_id, "")


@dataclass(frozen=True)
class CatalogDirectory:
    products: dict[UUID, ProductModel]

    @classmethod
    def load(cls) -> "CatalogDirectory":
        return cls({product.id: product for product in ProductModel.objects.all()})

    def get(self, product_id: UUID) -> ProductModel | None:
        return self.products.get(product_id)

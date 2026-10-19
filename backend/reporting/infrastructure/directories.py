from dataclasses import dataclass
from uuid import UUID

from accounts.infrastructure.models import UserModel


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

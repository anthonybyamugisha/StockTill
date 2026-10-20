from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Entity:
    id: UUID = field(default_factory=uuid4)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class AggregateRoot(Entity):
    """Marker base class for aggregate roots."""

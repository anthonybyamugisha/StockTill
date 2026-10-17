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


@dataclass
class AggregateRoot(Entity):
    _domain_events: list[Any] = field(default_factory=list, init=False, repr=False)

    def add_domain_event(self, event: Any) -> None:
        self._domain_events.append(event)

    def clear_domain_events(self) -> list[Any]:
        events = self._domain_events[:]
        self._domain_events.clear()
        return events

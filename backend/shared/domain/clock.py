from abc import ABC, abstractmethod
from datetime import UTC, datetime


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class UnitOfWork(AbstractContextManager[None], ABC):
    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass

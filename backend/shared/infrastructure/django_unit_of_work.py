from django.db import transaction

from shared.domain.unit_of_work import UnitOfWork


class DjangoUnitOfWork(UnitOfWork):
    def __init__(self, using: str = "default"):
        self._transaction = transaction.atomic(using=using)

    def __enter__(self):
        self._transaction.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._transaction.__exit__(exc_type, exc_val, exc_tb)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        transaction.set_rollback(True)

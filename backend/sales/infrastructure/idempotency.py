from uuid import UUID

from django.core.cache import cache

from sales.application.ports import IdempotencyPort


class CacheIdempotencyPort(IdempotencyPort):
    PREFIX = "idempotency:"
    TTL = 86400

    def exists(self, key: str) -> bool:
        return cache.get(f"{self.PREFIX}{key}") is not None

    def store(self, key: str, sale_id: UUID) -> None:
        cache.set(f"{self.PREFIX}{key}", str(sale_id), timeout=self.TTL)

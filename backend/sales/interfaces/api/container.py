from sales.application.use_cases import CompleteSaleUseCase, RefundSaleUseCase, VoidSaleUseCase
from sales.infrastructure.adapters import CatalogAdapter, InventoryAdapter
from sales.infrastructure.idempotency import CacheIdempotencyPort
from sales.infrastructure.receipt_number import DatabaseReceiptNumberPort
from sales.infrastructure.repository import DjangoRefundRepository, DjangoSaleRepository
from shared.domain.clock import SystemClock
from shared.infrastructure.audit import build_audit_recorder


def build_complete_sale_use_case() -> CompleteSaleUseCase:
    return CompleteSaleUseCase(
        DjangoSaleRepository(),
        InventoryAdapter(),
        CatalogAdapter(),
        DatabaseReceiptNumberPort(),
        CacheIdempotencyPort(),
        SystemClock(),
        build_audit_recorder(),
    )


def build_refund_sale_use_case() -> RefundSaleUseCase:
    return RefundSaleUseCase(
        DjangoSaleRepository(),
        DjangoRefundRepository(),
        InventoryAdapter(),
        SystemClock(),
        build_audit_recorder(),
    )


def build_void_sale_use_case() -> VoidSaleUseCase:
    return VoidSaleUseCase(
        DjangoSaleRepository(),
        InventoryAdapter(),
        SystemClock(),
        build_audit_recorder(),
    )

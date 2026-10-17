from decimal import Decimal
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.application.commands import (
    CompleteSaleCommand,
    LineItem,
    PaymentInput,
    RefundSaleCommand,
    VoidSaleCommand,
)
from sales.application.use_cases import CompleteSaleUseCase, RefundSaleUseCase, VoidSaleUseCase
from sales.domain.entities import DiscountType, PaymentMethod
from sales.infrastructure.adapters import CatalogAdapter, InventoryAdapter
from sales.infrastructure.idempotency import CacheIdempotencyPort
from sales.infrastructure.receipt_number import DatabaseReceiptNumberPort
from sales.infrastructure.repository import DjangoRefundRepository, DjangoSaleRepository
from sales.interfaces.api.serializers import (
    CompleteSaleSerializer,
    RefundSaleSerializer,
    SaleSerializer,
    VoidSaleSerializer,
)
from shared.domain.clock import SystemClock
from shared.domain.money import Money


class SaleListCreateView(APIView):
    def get(self, request):
        repo = DjangoSaleRepository()
        sales = repo.list_sales(
            cashier_id=UUID(request.query_params["cashier_id"]) if request.query_params.get("cashier_id") else None,
            status=request.query_params.get("status"),
            payment_method=request.query_params.get("payment_method"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
            receipt_number=request.query_params.get("receipt_number"),
        )
        return Response(SaleSerializer(sales, many=True).data)

    def post(self, request):
        serializer = CompleteSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lines = [
            LineItem(
                product_id=ln["product_id"],
                quantity=ln["quantity"],
                unit_price=Money(ln["unit_price"]),
                unit_cost=Money(ln["unit_cost"]),
                product_name=ln.get("product_name", ""),
                discount_type=DiscountType(ln["discount_type"]) if ln.get("discount_type") else None,
                discount_value=Decimal(str(ln["discount_value"])) if ln.get("discount_value") else None,
            )
            for ln in data["lines"]
        ]
        payments = [
            PaymentInput(
                method=PaymentMethod(p["method"]),
                amount=Money(p["amount"]),
                tendered=Money(p["tendered"]) if p.get("tendered") else None,
                reference=p.get("reference"),
                provider=p.get("provider"),
            )
            for p in data["payments"]
        ]

        use_case = CompleteSaleUseCase(
            DjangoSaleRepository(),
            InventoryAdapter(),
            CatalogAdapter(),
            DatabaseReceiptNumberPort(),
            CacheIdempotencyPort(),
            SystemClock(),
        )
        try:
            sale = use_case.execute(
                CompleteSaleCommand(
                    cashier_id=request.user.id,
                    lines=lines,
                    payments=payments,
                    idempotency_key=data["idempotency_key"],
                    notes=data.get("notes", ""),
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class SaleDetailView(APIView):
    def get(self, request, sale_id):
        repo = DjangoSaleRepository()
        sale = repo.get_by_id(sale_id)
        if sale is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(SaleSerializer(sale).data)


class RefundSaleView(APIView):
    def post(self, request):
        serializer = RefundSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = RefundSaleUseCase(
            DjangoSaleRepository(), DjangoRefundRepository(), InventoryAdapter(), SystemClock()
        )
        try:
            refund = use_case.execute(
                RefundSaleCommand(
                    sale_id=data["sale_id"],
                    line_id=data.get("line_id"),
                    quantity=data["quantity"],
                    reason=data["reason"],
                    restock=data["restock"],
                    user_id=request.user.id,
                )
            )
        except (ValueError, Exception) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"id": str(refund.id), "status": "refunded"}, status=status.HTTP_201_CREATED)


class VoidSaleView(APIView):
    def post(self, request):
        serializer = VoidSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = VoidSaleUseCase(DjangoSaleRepository(), InventoryAdapter(), SystemClock())
        try:
            sale = use_case.execute(
                VoidSaleCommand(
                    sale_id=data["sale_id"],
                    reason=data["reason"],
                    user_id=request.user.id,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SaleSerializer(sale).data)

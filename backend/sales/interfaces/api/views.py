from decimal import Decimal

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
from sales.infrastructure.adapters import InventoryAdapter
from sales.infrastructure.repository import DjangoRefundRepository, DjangoSaleRepository
from sales.interfaces.api.serializers import (
    CompleteSaleSerializer,
    RefundSaleSerializer,
    SaleSerializer,
    VoidSaleSerializer,
)
from shared.domain.money import Money


class SaleListCreateView(APIView):
    def get(self, request):
        repo = DjangoSaleRepository()
        sales = repo.list_sales(
            cashier_id=request.query_params.get("cashier_id"),
            status=request.query_params.get("status"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
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
                discount_type=ln.get("discount_type"),
                discount_value=Decimal(str(ln["discount_value"])) if ln.get("discount_value") else None,
            )
            for ln in data["lines"]
        ]
        payments = [
            PaymentInput(
                method=p["method"],
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
            None,
            None,
        )
        sale = use_case.execute(
            CompleteSaleCommand(
                cashier_id=request.user.id,
                lines=lines,
                payments=payments,
                idempotency_key=data["idempotency_key"],
            )
        )
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
            DjangoSaleRepository(), DjangoRefundRepository(), InventoryAdapter()
        )
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
        return Response({"id": str(refund.id), "status": "refunded"}, status=status.HTTP_201_CREATED)


class VoidSaleView(APIView):
    def post(self, request):
        serializer = VoidSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = VoidSaleUseCase(DjangoSaleRepository(), InventoryAdapter())
        sale = use_case.execute(
            VoidSaleCommand(
                sale_id=data["sale_id"],
                reason=data["reason"],
                user_id=request.user.id,
            )
        )
        return Response(SaleSerializer(sale).data)

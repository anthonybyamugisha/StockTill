from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.domain.entities import Role
from accounts.interfaces.api.permissions import IsManager
from sales.infrastructure.adapters import ShiftAdapter
from sales.infrastructure.repository import DjangoSaleRepository
from sales.interfaces.api.container import (
    build_complete_sale_use_case,
    build_refund_sale_use_case,
    build_void_sale_use_case,
)
from sales.interfaces.api.discount_limits import cashier_discount_limit
from sales.interfaces.api.filters import parse_status_filter
from sales.interfaces.api.request_mapping import (
    to_complete_sale_command,
    to_refund_sale_command,
    to_void_sale_command,
)
from sales.interfaces.api.serializers import (
    CompleteSaleSerializer,
    RefundSaleSerializer,
    SaleSerializer,
    VoidSaleSerializer,
)
from shared.interfaces.api.errors import domain_errors_to_bad_request


class SaleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            status_filter = parse_status_filter(request.query_params.get("status"))
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        cashier_id = request.user.id
        if request.user.role != Role.CASHIER.value:
            raw_cashier_id = request.query_params.get("cashier_id")
            if raw_cashier_id:
                try:
                    cashier_id = UUID(raw_cashier_id)
                except (TypeError, ValueError):
                    return Response(
                        {"detail": "Invalid cashier id"}, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                cashier_id = None

        repo = DjangoSaleRepository()
        sales = repo.list_sales(
            cashier_id=cashier_id,
            status=status_filter,
            payment_method=request.query_params.get("payment_method"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
            receipt_number=request.query_params.get("receipt_number"),
        )
        return Response(SaleSerializer(sales, many=True).data)

    @domain_errors_to_bad_request
    def post(self, request):
        serializer = CompleteSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = to_complete_sale_command(
            serializer.validated_data,
            cashier_id=request.user.id,
            shift_id=ShiftAdapter().open_shift_id(request.user.id),
            max_discount_percent=cashier_discount_limit(request.user),
        )
        sale = build_complete_sale_use_case().execute(command)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class SaleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sale_id):
        repo = DjangoSaleRepository()
        sale = repo.get_by_id(sale_id)
        if sale is None or (
            request.user.role == Role.CASHIER.value and sale.cashier_id != request.user.id
        ):
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(SaleSerializer(sale).data)


class RefundSaleView(APIView):
    permission_classes = [IsManager]

    @domain_errors_to_bad_request
    def post(self, request):
        serializer = RefundSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = build_refund_sale_use_case().execute(
            to_refund_sale_command(serializer.validated_data, user_id=request.user.id)
        )
        return Response(
            {"id": str(refund.id), "status": "refunded"}, status=status.HTTP_201_CREATED
        )


class VoidSaleView(APIView):
    permission_classes = [IsManager]

    @domain_errors_to_bad_request
    def post(self, request):
        serializer = VoidSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = build_void_sale_use_case().execute(
            to_void_sale_command(serializer.validated_data, user_id=request.user.id)
        )
        return Response(SaleSerializer(sale).data)

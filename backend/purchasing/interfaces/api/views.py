from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsManager
from purchasing.application.commands import (
    CancelPurchaseOrderCommand,
    CreatePurchaseOrderCommand,
    CreateSupplierCommand,
    PurchaseOrderLineInput,
    ReceivePurchaseOrderCommand,
    UpdateSupplierCommand,
)
from purchasing.application.use_cases import (
    CancelPurchaseOrderUseCase,
    CreatePurchaseOrderUseCase,
    CreateSupplierUseCase,
    GetPurchaseOrderUseCase,
    GetSupplierUseCase,
    ListPurchaseOrdersUseCase,
    ListSuppliersUseCase,
    MarkPurchaseOrderOrderedUseCase,
    ReceivePurchaseOrderUseCase,
    UpdateSupplierUseCase,
)
from purchasing.domain.errors import PurchaseOrderNotFoundError, SupplierNotFoundError
from purchasing.infrastructure.adapters import InventoryStockIntakeAdapter
from purchasing.infrastructure.repository import (
    DjangoPurchaseOrderRepository,
    DjangoSupplierRepository,
)
from purchasing.interfaces.api.serializers import (
    CancelPurchaseOrderSerializer,
    PurchaseOrderCreateSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
    SupplierWriteSerializer,
)
from shared.domain.clock import SystemClock
from shared.domain.money import Money


def _error(error: Exception) -> Response:
    code = status.HTTP_400_BAD_REQUEST
    if isinstance(error, (SupplierNotFoundError, PurchaseOrderNotFoundError)):
        code = status.HTTP_404_NOT_FOUND
    return Response({"detail": str(error)}, status=code)


class SupplierListCreateView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        search = request.query_params.get("search")
        suppliers = ListSuppliersUseCase(DjangoSupplierRepository()).execute(search=search)
        return Response(SupplierSerializer(suppliers, many=True).data)

    def post(self, request):
        serializer = SupplierWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            supplier = CreateSupplierUseCase(DjangoSupplierRepository(), SystemClock()).execute(
                CreateSupplierCommand(
                    name=data["name"],
                    contact_name=data["contact_name"],
                    email=data["email"],
                    phone=data["phone"],
                    address=data["address"],
                )
            )
        except Exception as error:
            return _error(error)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    permission_classes = [IsManager]

    def get(self, request, supplier_id):
        try:
            supplier = GetSupplierUseCase(DjangoSupplierRepository()).execute(supplier_id)
        except Exception as error:
            return _error(error)
        return Response(SupplierSerializer(supplier).data)

    def patch(self, request, supplier_id):
        serializer = SupplierWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            supplier = UpdateSupplierUseCase(DjangoSupplierRepository()).execute(
                UpdateSupplierCommand(
                    supplier_id=supplier_id,
                    name=data["name"],
                    contact_name=data["contact_name"],
                    email=data["email"],
                    phone=data["phone"],
                    address=data["address"],
                )
            )
        except Exception as error:
            return _error(error)
        return Response(SupplierSerializer(supplier).data)


class PurchaseOrderListCreateView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        orders = ListPurchaseOrdersUseCase(DjangoPurchaseOrderRepository()).execute()
        return Response(PurchaseOrderSerializer(orders, many=True).data)

    def post(self, request):
        serializer = PurchaseOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lines = [
            PurchaseOrderLineInput(
                product_id=line["product_id"],
                product_name=line.get("product_name", ""),
                quantity=line["quantity"],
                unit_cost=Money(line["unit_cost"]),
            )
            for line in data["lines"]
        ]
        try:
            order = CreatePurchaseOrderUseCase(
                DjangoPurchaseOrderRepository(),
                DjangoSupplierRepository(),
                SystemClock(),
            ).execute(
                CreatePurchaseOrderCommand(
                    supplier_id=data["supplier_id"],
                    lines=lines,
                    reference=data["reference"],
                    notes=data["notes"],
                )
            )
        except Exception as error:
            return _error(error)
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(APIView):
    permission_classes = [IsManager]

    def get(self, request, purchase_order_id):
        try:
            order = GetPurchaseOrderUseCase(DjangoPurchaseOrderRepository()).execute(
                purchase_order_id
            )
        except Exception as error:
            return _error(error)
        return Response(PurchaseOrderSerializer(order).data)


class PurchaseOrderOrderView(APIView):
    permission_classes = [IsManager]

    def post(self, request, purchase_order_id):
        try:
            order = MarkPurchaseOrderOrderedUseCase(
                DjangoPurchaseOrderRepository(), SystemClock()
            ).execute(purchase_order_id)
        except Exception as error:
            return _error(error)
        return Response(PurchaseOrderSerializer(order).data)


class PurchaseOrderReceiveView(APIView):
    permission_classes = [IsManager]

    def post(self, request, purchase_order_id):
        try:
            order = ReceivePurchaseOrderUseCase(
                DjangoPurchaseOrderRepository(),
                InventoryStockIntakeAdapter(),
                SystemClock(),
            ).execute(
                ReceivePurchaseOrderCommand(
                    purchase_order_id=purchase_order_id,
                    user_id=request.user.id,
                )
            )
        except Exception as error:
            return _error(error)
        return Response(PurchaseOrderSerializer(order).data)


class PurchaseOrderCancelView(APIView):
    permission_classes = [IsManager]

    def post(self, request, purchase_order_id):
        serializer = CancelPurchaseOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = CancelPurchaseOrderUseCase(DjangoPurchaseOrderRepository()).execute(
                CancelPurchaseOrderCommand(
                    purchase_order_id=purchase_order_id,
                    reason=serializer.validated_data["reason"],
                )
            )
        except Exception as error:
            return _error(error)
        return Response(PurchaseOrderSerializer(order).data)

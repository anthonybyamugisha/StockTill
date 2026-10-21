from uuid import UUID

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsManager
from purchasing.application.commands import (
    CancelPurchaseOrderCommand,
    CreatePurchaseOrderCommand,
    CreateSupplierCommand,
    CreateSupplierInvoiceCommand,
    PurchaseOrderLineInput,
    ReceivePurchaseOrderCommand,
    RecordSupplierInvoicePaymentCommand,
    SupplierInvoiceLineInput,
    UpdateSupplierCommand,
    VoidSupplierInvoiceCommand,
)
from purchasing.application.use_cases import (
    CancelPurchaseOrderUseCase,
    CreatePurchaseOrderUseCase,
    CreateSupplierInvoiceUseCase,
    CreateSupplierUseCase,
    GetPurchaseOrderUseCase,
    GetSupplierInvoiceUseCase,
    GetSupplierUseCase,
    ListPurchaseOrdersUseCase,
    ListSupplierInvoicesUseCase,
    ListSuppliersUseCase,
    MarkPurchaseOrderOrderedUseCase,
    ReceivePurchaseOrderUseCase,
    RecordSupplierInvoicePaymentUseCase,
    UpdateSupplierUseCase,
    VoidSupplierInvoiceUseCase,
)
from purchasing.domain.entities import SupplierInvoiceStatus
from purchasing.domain.errors import (
    PurchaseOrderNotFoundError,
    SupplierInvoiceNotFoundError,
    SupplierNotFoundError,
)
from purchasing.infrastructure.adapters import InventoryStockIntakeAdapter
from purchasing.infrastructure.repository import (
    DjangoPurchaseOrderRepository,
    DjangoSupplierInvoiceRepository,
    DjangoSupplierRepository,
)
from purchasing.interfaces.api.serializers import (
    CancelPurchaseOrderSerializer,
    PurchaseOrderCreateSerializer,
    PurchaseOrderSerializer,
    SupplierInvoiceCreateSerializer,
    SupplierInvoicePaymentSerializer,
    SupplierInvoiceSerializer,
    SupplierSerializer,
    SupplierWriteSerializer,
    VoidSupplierInvoiceSerializer,
)
from shared.domain.clock import SystemClock
from shared.domain.money import Money
from shared.infrastructure.audit import build_audit_recorder


def _actor_id(request):
    return request.user.id if request.user.is_authenticated else None


def _error(error: Exception) -> Response:
    code = status.HTTP_400_BAD_REQUEST
    if isinstance(
        error,
        (SupplierNotFoundError, PurchaseOrderNotFoundError, SupplierInvoiceNotFoundError),
    ):
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
            supplier = CreateSupplierUseCase(
                DjangoSupplierRepository(), SystemClock(), build_audit_recorder()
            ).execute(
                CreateSupplierCommand(
                    name=data["name"],
                    contact_name=data["contact_name"],
                    email=data["email"],
                    phone=data["phone"],
                    address=data["address"],
                    actor_id=_actor_id(request),
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
            supplier = UpdateSupplierUseCase(
                DjangoSupplierRepository(), build_audit_recorder()
            ).execute(
                UpdateSupplierCommand(
                    supplier_id=supplier_id,
                    name=data["name"],
                    contact_name=data["contact_name"],
                    email=data["email"],
                    phone=data["phone"],
                    address=data["address"],
                    actor_id=_actor_id(request),
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
                build_audit_recorder(),
            ).execute(
                CreatePurchaseOrderCommand(
                    supplier_id=data["supplier_id"],
                    lines=lines,
                    reference=data["reference"],
                    notes=data["notes"],
                    actor_id=_actor_id(request),
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
                DjangoPurchaseOrderRepository(), SystemClock(), build_audit_recorder()
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
                build_audit_recorder(),
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
            order = CancelPurchaseOrderUseCase(
                DjangoPurchaseOrderRepository(), build_audit_recorder()
            ).execute(
                CancelPurchaseOrderCommand(
                    purchase_order_id=purchase_order_id,
                    reason=serializer.validated_data["reason"],
                    actor_id=_actor_id(request),
                )
            )
        except Exception as error:
            return _error(error)
        return Response(PurchaseOrderSerializer(order).data)


class SupplierInvoiceListCreateView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        status_param = request.query_params.get("status")
        try:
            invoice_status = SupplierInvoiceStatus(status_param) if status_param else None
        except ValueError:
            return Response(
                {"detail": "Unknown invoice status"}, status=status.HTTP_400_BAD_REQUEST
            )
        supplier_id = None
        if request.query_params.get("supplier_id"):
            try:
                supplier_id = UUID(request.query_params["supplier_id"])
            except ValueError:
                return Response(
                    {"detail": "Invalid supplier id"}, status=status.HTTP_400_BAD_REQUEST
                )
        invoices = ListSupplierInvoicesUseCase(DjangoSupplierInvoiceRepository()).execute(
            supplier_id=supplier_id, status=invoice_status
        )
        return Response(SupplierInvoiceSerializer(invoices, many=True).data)

    def post(self, request):
        serializer = SupplierInvoiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lines = [
            SupplierInvoiceLineInput(
                product_id=line.get("product_id"),
                product_name=line.get("product_name", ""),
                description=line.get("description", ""),
                quantity=line["quantity"],
                unit_cost=Money(line["unit_cost"]),
            )
            for line in data["lines"]
        ]
        try:
            invoice = CreateSupplierInvoiceUseCase(
                DjangoSupplierInvoiceRepository(),
                DjangoSupplierRepository(),
                SystemClock(),
                build_audit_recorder(),
            ).execute(
                CreateSupplierInvoiceCommand(
                    supplier_id=data["supplier_id"],
                    invoice_number=data["invoice_number"],
                    lines=lines,
                    invoice_date=data.get("invoice_date"),
                    due_date=data.get("due_date"),
                    purchase_order_id=data.get("purchase_order_id"),
                    notes=data.get("notes", ""),
                    actor_id=_actor_id(request),
                )
            )
        except Exception as error:
            return _error(error)
        return Response(SupplierInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class SupplierInvoiceDetailView(APIView):
    permission_classes = [IsManager]

    def get(self, request, invoice_id):
        try:
            invoice = GetSupplierInvoiceUseCase(DjangoSupplierInvoiceRepository()).execute(
                invoice_id
            )
        except Exception as error:
            return _error(error)
        return Response(SupplierInvoiceSerializer(invoice).data)


class SupplierInvoicePaymentView(APIView):
    permission_classes = [IsManager]

    def post(self, request, invoice_id):
        serializer = SupplierInvoicePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice = RecordSupplierInvoicePaymentUseCase(
                DjangoSupplierInvoiceRepository(), build_audit_recorder()
            ).execute(
                RecordSupplierInvoicePaymentCommand(
                    invoice_id=invoice_id,
                    amount=Money(serializer.validated_data["amount"]),
                    actor_id=_actor_id(request),
                )
            )
        except Exception as error:
            return _error(error)
        return Response(SupplierInvoiceSerializer(invoice).data)


class SupplierInvoiceVoidView(APIView):
    permission_classes = [IsManager]

    def post(self, request, invoice_id):
        serializer = VoidSupplierInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice = VoidSupplierInvoiceUseCase(
                DjangoSupplierInvoiceRepository(), build_audit_recorder()
            ).execute(
                VoidSupplierInvoiceCommand(
                    invoice_id=invoice_id,
                    reason=serializer.validated_data["reason"],
                    actor_id=_actor_id(request),
                )
            )
        except Exception as error:
            return _error(error)
        return Response(SupplierInvoiceSerializer(invoice).data)

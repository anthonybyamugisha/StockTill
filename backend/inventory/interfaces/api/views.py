from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsAdmin, IsManager
from inventory.application.commands import AdjustStockCommand
from inventory.application.use_cases import AdjustStockUseCase, RebuildStockCacheUseCase
from inventory.domain.entities import MovementType
from inventory.infrastructure.adapters import CatalogProductInfoAdapter
from inventory.infrastructure.repository import (
    DjangoStockItemRepository,
    DjangoStockMovementRepository,
)
from inventory.interfaces.api.serializers import (
    StockAdjustmentSerializer,
    StockItemSerializer,
    StockMovementSerializer,
    ValuationSerializer,
)
from shared.domain.clock import SystemClock
from shared.domain.money import Money
from shared.infrastructure.audit import build_audit_recorder


class StockAdjustmentView(APIView):
    permission_classes = [IsManager]

    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = AdjustStockUseCase(
            DjangoStockItemRepository(),
            DjangoStockMovementRepository(),
            CatalogProductInfoAdapter(),
            SystemClock(),
            build_audit_recorder(),
        )
        try:
            movement = use_case.execute(
                AdjustStockCommand(
                    product_id=data["product_id"],
                    quantity=data["quantity"],
                    movement_type=MovementType(data["movement_type"]),
                    reason=data["reason"],
                    reference=data.get("reference"),
                    unit_cost=Money(data["unit_cost"]) if data.get("unit_cost") else None,
                    user_id=request.user.id if request.user.is_authenticated else None,
                    notes=data.get("notes", ""),
                )
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


def _serialize_items(items) -> list[dict]:
    labels = CatalogProductInfoAdapter().get_product_labels(item.product_id for item in items)
    return StockItemSerializer(items, many=True, context={"labels": labels}).data


class StockItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = DjangoStockItemRepository()
        items = repo.list_all()
        return Response(_serialize_items(items))


class StockItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        repo = DjangoStockItemRepository()
        item = repo.get_by_product(product_id)
        if item is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_items([item])[0])


class StockHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        repo = DjangoStockMovementRepository()
        movements = repo.list_by_product(product_id)
        return Response(StockMovementSerializer(movements, many=True).data)


class LowStockView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = DjangoStockItemRepository()
        items = repo.list_low_stock()
        return Response(_serialize_items(items))


class OutOfStockView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = DjangoStockItemRepository()
        items = repo.list_out_of_stock()
        return Response(_serialize_items(items))


class InventoryValuationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo = DjangoStockItemRepository()
        valuation = repo.get_valuation()
        return Response(ValuationSerializer(valuation).data)


class RebuildStockCacheView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        use_case = RebuildStockCacheUseCase(
            DjangoStockItemRepository(), DjangoStockMovementRepository()
        )
        count = use_case.execute()
        return Response({"rebuilt": count})

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.application.commands import AdjustStockCommand
from inventory.application.use_cases import AdjustStockUseCase
from inventory.domain.entities import MovementType
from inventory.infrastructure.repository import (
    DjangoStockItemRepository,
    DjangoStockMovementRepository,
)
from inventory.interfaces.api.serializers import (
    StockAdjustmentSerializer,
    StockItemSerializer,
    StockMovementSerializer,
)
from shared.domain.money import Money


class StockAdjustmentView(APIView):
    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = AdjustStockUseCase(
            DjangoStockItemRepository(), DjangoStockMovementRepository()
        )
        movement = use_case.execute(
            AdjustStockCommand(
                product_id=data["product_id"],
                quantity=data["quantity"],
                movement_type=MovementType(data["movement_type"]),
                reason=data["reason"],
                reference=data.get("reference"),
                unit_cost=Money(data["unit_cost"]) if data.get("unit_cost") else None,
                user_id=request.user.id if request.user.is_authenticated else None,
            )
        )
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class StockItemDetailView(APIView):
    def get(self, request, product_id):
        repo = DjangoStockItemRepository()
        item = repo.get_by_product(product_id)
        if item is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(StockItemSerializer(item).data)


class LowStockView(APIView):
    def get(self, request):
        repo = DjangoStockItemRepository()
        items = repo.list_low_stock()
        return Response(StockItemSerializer(items, many=True).data)


class OutOfStockView(APIView):
    def get(self, request):
        repo = DjangoStockItemRepository()
        items = repo.list_out_of_stock()
        return Response(StockItemSerializer(items, many=True).data)

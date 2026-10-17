from rest_framework import serializers

from inventory.domain.entities import MovementType, StockItem, StockMovement


class StockAdjustmentSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField()
    movement_type = serializers.ChoiceField(choices=[t.value for t in MovementType])
    reason = serializers.CharField(max_length=500)
    reference = serializers.CharField(max_length=100, allow_null=True, required=False)
    unit_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, allow_null=True, required=False
    )
    notes = serializers.CharField(max_length=500, allow_blank=True, required=False)


class StockMovementSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField()
    movement_type = serializers.CharField()
    reason = serializers.CharField()
    reference = serializers.CharField(allow_null=True)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    user_id = serializers.UUIDField(allow_null=True)
    timestamp = serializers.DateTimeField(read_only=True)
    notes = serializers.CharField(allow_blank=True)


class StockItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity_on_hand = serializers.IntegerField()
    reserved_quantity = serializers.IntegerField()
    available_quantity = serializers.IntegerField(read_only=True)


class ValuationSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    by_product = serializers.ListField()

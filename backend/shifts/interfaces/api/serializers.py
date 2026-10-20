from rest_framework import serializers


class OpenShiftSerializer(serializers.Serializer):
    opening_float = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    notes = serializers.CharField(allow_blank=True, required=False)


class CloseShiftSerializer(serializers.Serializer):
    shift_id = serializers.UUIDField()
    counted_cash = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    notes = serializers.CharField(allow_blank=True, required=False)


class CashMovementInputSerializer(serializers.Serializer):
    shift_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=["payout", "cash_in"])
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    reason = serializers.CharField(allow_blank=True, required=False)


class CashMovementSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reason = serializers.CharField()
    created_at = serializers.DateTimeField()


class ShiftSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    cashier_id = serializers.UUIDField()
    status = serializers.CharField()
    opening_float = serializers.DecimalField(max_digits=14, decimal_places=2)
    counted_cash = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    notes = serializers.CharField()
    opened_at = serializers.DateTimeField()
    closed_at = serializers.DateTimeField(allow_null=True)
    cash_movements = CashMovementSerializer(many=True)

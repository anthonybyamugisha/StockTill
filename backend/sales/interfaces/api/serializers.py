from rest_framework import serializers

from sales.domain.entities import DiscountType, PaymentMethod


class SaleLineSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_type = serializers.SerializerMethodField()
    discount_value = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)

    def get_discount_type(self, obj) -> str | None:
        return obj.discount.type.value if obj.discount else None

    def get_discount_value(self, obj) -> str | None:
        return str(obj.discount.value) if obj.discount else None

    def get_discount_amount(self, obj) -> str:
        return str(obj.discount.amount.amount) if obj.discount else "0.00"


class PaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    method = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    tendered = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    change = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    reference = serializers.CharField(allow_null=True)
    provider = serializers.CharField(allow_null=True)


class RefundSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    sale_id = serializers.UUIDField()
    line_id = serializers.UUIDField(allow_null=True)
    quantity = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reason = serializers.CharField()
    restock = serializers.BooleanField()
    user_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()


class SaleSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    receipt_number = serializers.CharField()
    cashier_id = serializers.UUIDField()
    status = serializers.CharField()
    lines = SaleLineSerializer(many=True)
    payments = PaymentSerializer(many=True)
    refunds = RefundSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=14, decimal_places=2)
    refundable_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_profit = serializers.DecimalField(max_digits=14, decimal_places=2)
    notes = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()


class LineItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    product_name = serializers.CharField(required=False, allow_blank=True)
    discount_type = serializers.ChoiceField(
        choices=[t.value for t in DiscountType], allow_null=True, required=False
    )
    discount_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, allow_null=True, required=False
    )


class PaymentInputSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[m.value for m in PaymentMethod])
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    tendered = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, allow_null=True, required=False
    )
    reference = serializers.CharField(max_length=200, allow_null=True, required=False)
    provider = serializers.CharField(max_length=100, allow_null=True, required=False)


class CompleteSaleSerializer(serializers.Serializer):
    lines = LineItemSerializer(many=True)
    payments = PaymentInputSerializer(many=True)
    idempotency_key = serializers.CharField(max_length=100)
    notes = serializers.CharField(allow_blank=True, required=False)


class RefundSaleSerializer(serializers.Serializer):
    sale_id = serializers.UUIDField()
    line_id = serializers.UUIDField(allow_null=True, required=False)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)
    restock = serializers.BooleanField(default=False)


class VoidSaleSerializer(serializers.Serializer):
    sale_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500)

from rest_framework import serializers


class LineItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    discount_type = serializers.ChoiceField(
        choices=["percentage", "fixed"], allow_null=True, required=False
    )
    discount_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, allow_null=True, required=False
    )


class PaymentInputSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=["cash", "mobile_money", "card", "bank_transfer"])
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


class SaleLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_type = serializers.CharField(allow_null=True)
    discount_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class PaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    method = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    tendered = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    change = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    reference = serializers.CharField(allow_null=True)
    provider = serializers.CharField(allow_null=True)


class SaleSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    receipt_number = serializers.CharField()
    cashier_id = serializers.UUIDField()
    status = serializers.CharField()
    lines = SaleLineSerializer(many=True)
    payments = PaymentSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    created_at = serializers.DateTimeField()


class RefundSaleSerializer(serializers.Serializer):
    sale_id = serializers.UUIDField()
    line_id = serializers.UUIDField(allow_null=True, required=False)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)
    restock = serializers.BooleanField(default=False)


class VoidSaleSerializer(serializers.Serializer):
    sale_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500)

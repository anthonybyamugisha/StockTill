from decimal import Decimal

from rest_framework import serializers

from payments.domain.entities import MobileNetwork, PaymentMethod


class SalePayloadLineSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    discount_type = serializers.ChoiceField(
        choices=["percentage", "fixed"], required=False, allow_null=True
    )
    discount_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False, allow_null=True
    )


class SalePayloadSerializer(serializers.Serializer):
    lines = SalePayloadLineSerializer(many=True, allow_empty=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CreatePaymentIntentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[PaymentMethod.MOBILE_MONEY.value])
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    phone = serializers.CharField(max_length=30)
    network = serializers.ChoiceField(choices=[network.value for network in MobileNetwork])
    idempotency_key = serializers.CharField(max_length=100)
    sale = SalePayloadSerializer()


class PaymentIntentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tx_ref = serializers.CharField()
    method = serializers.CharField()
    network = serializers.CharField(allow_null=True)
    phone = serializers.CharField()
    amount = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    status = serializers.CharField()
    provider = serializers.CharField()
    gateway_reference = serializers.CharField(allow_null=True)
    checkout_url = serializers.CharField(allow_null=True)
    failure_reason = serializers.CharField()
    sale_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)

    def get_amount(self, obj) -> str:
        return str(obj.amount.amount)

    def get_currency(self, obj) -> str:
        return obj.amount.currency


class CancelPaymentIntentSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)

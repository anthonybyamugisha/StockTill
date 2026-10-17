from rest_framework import serializers


class SupplierSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    contact_name = serializers.CharField()
    email = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class SupplierWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    contact_name = serializers.CharField(
        max_length=300, required=False, allow_blank=True, default=""
    )
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    address = serializers.CharField(required=False, allow_blank=True, default="")


class PurchaseOrderLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_cost = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    def get_unit_cost(self, obj) -> str:
        return str(obj.unit_cost.amount)

    def get_line_total(self, obj) -> str:
        return str(obj.line_total.amount)


class PurchaseOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    supplier_id = serializers.UUIDField(allow_null=True)
    supplier_name = serializers.CharField()
    status = serializers.CharField()
    reference = serializers.CharField()
    notes = serializers.CharField()
    total = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    ordered_at = serializers.DateTimeField(allow_null=True)
    received_at = serializers.DateTimeField(allow_null=True)
    lines = PurchaseOrderLineSerializer(many=True)

    def get_total(self, obj) -> str:
        return str(obj.total.amount)


class PurchaseOrderLineInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField(
        max_length=300, required=False, allow_blank=True, default=""
    )
    quantity = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField()
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = PurchaseOrderLineInputSerializer(many=True)


class CancelPurchaseOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")

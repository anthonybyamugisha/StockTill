from rest_framework import serializers


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=300)
    description = serializers.CharField(allow_blank=True)
    sku = serializers.CharField(max_length=100)
    barcode = serializers.CharField(max_length=100, allow_null=True, required=False)
    category_id = serializers.UUIDField(allow_null=True, required=False)
    buying_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    selling_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    minimum_stock_level = serializers.IntegerField(min_value=0)
    image_url = serializers.URLField(allow_null=True, required=False)
    is_active = serializers.BooleanField(read_only=True)


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    description = serializers.CharField(allow_blank=True, required=False)
    sku = serializers.CharField(max_length=100)
    barcode = serializers.CharField(max_length=100, allow_null=True, required=False)
    category_id = serializers.UUIDField(allow_null=True, required=False)
    buying_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    selling_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    minimum_stock_level = serializers.IntegerField(min_value=0, required=False)
    image_url = serializers.URLField(allow_null=True, required=False)

from rest_framework import serializers


class CategorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, required=False)
    parent_id = serializers.UUIDField(allow_null=True, required=False)
    is_active = serializers.BooleanField(read_only=True)


class ProductListSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=300)
    sku = serializers.CharField(max_length=100)
    barcode = serializers.CharField(allow_null=True, required=False)
    selling_price = serializers.DecimalField(max_digits=14, decimal_places=2)
    buying_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    minimum_stock_level = serializers.IntegerField()
    category_id = serializers.UUIDField(allow_null=True, required=False)
    image_url = serializers.URLField(allow_null=True, required=False)
    is_active = serializers.BooleanField(read_only=True)


class ProductDetailSerializer(ProductListSerializer):
    description = serializers.CharField(allow_blank=True)


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300)
    sku = serializers.CharField(max_length=100)
    selling_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    buying_cost = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    description = serializers.CharField(allow_blank=True, required=False)
    barcode = serializers.CharField(
        max_length=100, allow_null=True, allow_blank=True, required=False
    )
    category_id = serializers.UUIDField(allow_null=True, required=False)
    minimum_stock_level = serializers.IntegerField(min_value=0, required=False)
    image_url = serializers.URLField(allow_null=True, required=False)
    opening_stock = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate_barcode(self, value: str | None) -> str | None:
        return value or None


class UpdateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=300, required=False)
    sku = serializers.CharField(max_length=100, required=False)
    selling_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False
    )
    buying_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False
    )
    description = serializers.CharField(allow_blank=True, required=False)
    barcode = serializers.CharField(
        max_length=100, allow_null=True, allow_blank=True, required=False
    )
    category_id = serializers.UUIDField(allow_null=True, required=False)
    minimum_stock_level = serializers.IntegerField(min_value=0, required=False)
    image_url = serializers.URLField(allow_null=True, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_barcode(self, value: str | None) -> str | None:
        return value or None


class CreateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, required=False)
    parent_id = serializers.UUIDField(allow_null=True, required=False)


class UpdateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    parent_id = serializers.UUIDField(allow_null=True, required=False)
    is_active = serializers.BooleanField(required=False)

from rest_framework import serializers


class SettingsSerializer(serializers.Serializer):
    business_name = serializers.CharField(max_length=200)
    address = serializers.CharField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(allow_blank=True)
    currency = serializers.CharField(max_length=3)
    receipt_header = serializers.CharField(allow_blank=True)
    receipt_footer = serializers.CharField(allow_blank=True)
    cashier_discount_limit = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    logo_url = serializers.URLField(allow_null=True, required=False)

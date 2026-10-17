from rest_framework import serializers


class SalesSummarySerializer(serializers.Serializer):
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_profit = serializers.DecimalField(max_digits=14, decimal_places=2)
    average_sale_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    date_from = serializers.DateField()
    date_to = serializers.DateField()


class TopProductSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class SalesByPaymentMethodSerializer(serializers.Serializer):
    method = serializers.CharField()
    count = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)


class DailySalesSerializer(serializers.Serializer):
    date = serializers.DateField()
    transaction_count = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)


class CashierSalesSerializer(serializers.Serializer):
    cashier_id = serializers.UUIDField()
    cashier_name = serializers.CharField()
    transaction_count = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)

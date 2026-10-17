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


class DashboardStatsSerializer(serializers.Serializer):
    today_sales = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    week_sales = serializers.IntegerField()
    week_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    month_sales = serializers.IntegerField()
    month_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_transactions = serializers.IntegerField()
    total_products = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()
    average_sale_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_profit = serializers.DecimalField(max_digits=14, decimal_places=2)


class ProfitReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    gross_profit = serializers.DecimalField(max_digits=14, decimal_places=2)


class InventoryReportSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()


class SalesReportRowSerializer(serializers.Serializer):
    receipt_number = serializers.CharField()
    date = serializers.DateTimeField()
    cashier_name = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    payment_method = serializers.CharField()
    status = serializers.CharField()


class LowStockItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    sku = serializers.CharField()
    quantity_on_hand = serializers.IntegerField()
    minimum_level = serializers.IntegerField()

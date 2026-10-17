import csv
from datetime import date
from io import StringIO

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsManager
from reporting.infrastructure.query_builders import SalesQueryBuilder
from reporting.interfaces.api.serializers import (
    CashierSalesSerializer,
    DailySalesSerializer,
    DashboardStatsSerializer,
    InventoryReportSerializer,
    LowStockItemSerializer,
    ProfitReportSerializer,
    SalesByPaymentMethodSerializer,
    SalesReportRowSerializer,
    SalesSummarySerializer,
    TopProductSerializer,
)


def parse_date(request, param, default):
    value = request.query_params.get(param)
    if value:
        return date.fromisoformat(value)
    return default


class SalesSummaryView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        summary = builder.get_sales_summary(date_from, date_to)
        return Response(SalesSummarySerializer(summary).data)


class TopProductsView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        limit = int(request.query_params.get("limit", 10))
        builder = SalesQueryBuilder()
        products = builder.get_top_products(date_from, date_to, limit)
        return Response(TopProductSerializer(products, many=True).data)


class SalesByPaymentMethodView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        data = builder.get_sales_by_payment_method(date_from, date_to)
        return Response(SalesByPaymentMethodSerializer(data, many=True).data)


class DailySalesView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        data = builder.get_daily_sales(date_from, date_to)
        return Response(DailySalesSerializer(data, many=True).data)


class CashierSalesView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        data = builder.get_cashier_sales(date_from, date_to)
        return Response(CashierSalesSerializer(data, many=True).data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        builder = SalesQueryBuilder()
        stats = builder.get_dashboard_stats()
        return Response(DashboardStatsSerializer(stats).data)


class ProfitReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        data = builder.get_profit_report(date_from, date_to)
        return Response(ProfitReportSerializer(data, many=True).data)


class InventoryReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        builder = SalesQueryBuilder()
        report = builder.get_inventory_report()
        return Response(InventoryReportSerializer(report).data)


class SalesReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        rows = builder.get_sales_report(date_from, date_to)
        return Response(SalesReportRowSerializer(rows, many=True).data)


class LowStockReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        builder = SalesQueryBuilder()
        items = builder.get_low_stock_items()
        return Response(LowStockItemSerializer(items, many=True).data)


class SalesReportCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        today = date.today()
        date_from = parse_date(request, "date_from", today.replace(day=1))
        date_to = parse_date(request, "date_to", today)
        builder = SalesQueryBuilder()
        rows = builder.get_sales_report(date_from, date_to)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Receipt", "Date", "Cashier", "Total", "Payment Method", "Status"])
        for row in rows:
            writer.writerow(
                [
                    row.receipt_number,
                    row.date.isoformat(),
                    row.cashier_name,
                    str(row.total),
                    row.payment_method,
                    row.status,
                ]
            )

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=sales_report.csv"
        return response

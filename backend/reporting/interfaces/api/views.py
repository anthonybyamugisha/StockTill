import csv
from io import StringIO

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsManager
from reporting.application.use_cases import (
    GetCashierSalesUseCase,
    GetDailySalesUseCase,
    GetDashboardStatsUseCase,
    GetInventoryReportUseCase,
    GetLowStockItemsUseCase,
    GetProfitReportUseCase,
    GetSalesByPaymentMethodUseCase,
    GetSalesReportUseCase,
    GetSalesSummaryUseCase,
    GetTopProductsUseCase,
)
from reporting.infrastructure.queries.cashier_sales import DjangoCashierSalesQuery
from reporting.infrastructure.queries.daily_sales import DjangoDailySalesQuery
from reporting.infrastructure.queries.dashboard import DjangoDashboardQuery
from reporting.infrastructure.queries.inventory_report import DjangoInventoryReportQuery
from reporting.infrastructure.queries.low_stock import DjangoLowStockQuery
from reporting.infrastructure.queries.payment_methods import DjangoPaymentMethodSalesQuery
from reporting.infrastructure.queries.profit import DjangoProfitReportQuery
from reporting.infrastructure.queries.sales_report import DjangoSalesReportQuery
from reporting.infrastructure.queries.sales_summary import DjangoSalesSummaryQuery
from reporting.infrastructure.queries.top_products import DjangoTopProductsQuery
from reporting.interfaces.api.date_range import DateRange
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


class SalesSummaryView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        summary = GetSalesSummaryUseCase(DjangoSalesSummaryQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(SalesSummarySerializer(summary).data)


class TopProductsView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        limit = int(request.query_params.get("limit", 10))
        products = GetTopProductsUseCase(DjangoTopProductsQuery()).execute(
            dates.date_from, dates.date_to, limit
        )
        return Response(TopProductSerializer(products, many=True).data)


class SalesByPaymentMethodView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetSalesByPaymentMethodUseCase(DjangoPaymentMethodSalesQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(SalesByPaymentMethodSerializer(data, many=True).data)


class DailySalesView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetDailySalesUseCase(DjangoDailySalesQuery()).execute(dates.date_from, dates.date_to)
        return Response(DailySalesSerializer(data, many=True).data)


class CashierSalesView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetCashierSalesUseCase(DjangoCashierSalesQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(CashierSalesSerializer(data, many=True).data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = GetDashboardStatsUseCase(DjangoDashboardQuery()).execute()
        return Response(DashboardStatsSerializer(stats).data)


class ProfitReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetProfitReportUseCase(DjangoProfitReportQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(ProfitReportSerializer(data, many=True).data)


class InventoryReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        report = GetInventoryReportUseCase(DjangoInventoryReportQuery()).execute()
        return Response(InventoryReportSerializer(report).data)


class SalesReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        rows = GetSalesReportUseCase(DjangoSalesReportQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(SalesReportRowSerializer(rows, many=True).data)


class LowStockReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        items = GetLowStockItemsUseCase(DjangoLowStockQuery()).execute()
        return Response(LowStockItemSerializer(items, many=True).data)


class SalesReportCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        rows = GetSalesReportUseCase(DjangoSalesReportQuery()).execute(
            dates.date_from, dates.date_to
        )

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

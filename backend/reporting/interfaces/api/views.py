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
from reporting.interfaces.api.csv_export import (
    write_cashier_sales_csv,
    write_daily_sales_csv,
    write_inventory_report_csv,
    write_low_stock_csv,
    write_payment_methods_csv,
    write_profit_report_csv,
    write_sales_report_csv,
    write_sales_summary_csv,
    write_top_products_csv,
)
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

CSV_CONTENT_TYPE = "text/csv"


def _csv_response(content: str, filename: str) -> HttpResponse:
    response = HttpResponse(content, content_type=CSV_CONTENT_TYPE)
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


class SalesSummaryView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        summary = GetSalesSummaryUseCase(DjangoSalesSummaryQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(SalesSummarySerializer(summary).data)


class SalesSummaryCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        summary = GetSalesSummaryUseCase(DjangoSalesSummaryQuery()).execute(
            dates.date_from, dates.date_to
        )
        return _csv_response(write_sales_summary_csv(summary), "sales_summary.csv")


class TopProductsView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        limit = int(request.query_params.get("limit", 10))
        products = GetTopProductsUseCase(DjangoTopProductsQuery()).execute(
            dates.date_from, dates.date_to, limit
        )
        return Response(TopProductSerializer(products, many=True).data)


class TopProductsCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        limit = int(request.query_params.get("limit", 10))
        data = GetTopProductsUseCase(DjangoTopProductsQuery()).execute(
            dates.date_from, dates.date_to, limit
        )
        return _csv_response(write_top_products_csv(data), "top_products.csv")


class SalesByPaymentMethodView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetSalesByPaymentMethodUseCase(DjangoPaymentMethodSalesQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(SalesByPaymentMethodSerializer(data, many=True).data)


class SalesByPaymentMethodCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetSalesByPaymentMethodUseCase(DjangoPaymentMethodSalesQuery()).execute(
            dates.date_from, dates.date_to
        )
        return _csv_response(write_payment_methods_csv(data), "sales_by_payment_method.csv")


class DailySalesView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetDailySalesUseCase(DjangoDailySalesQuery()).execute(dates.date_from, dates.date_to)
        return Response(DailySalesSerializer(data, many=True).data)


class DailySalesCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetDailySalesUseCase(DjangoDailySalesQuery()).execute(dates.date_from, dates.date_to)
        return _csv_response(write_daily_sales_csv(data), "daily_sales.csv")


class CashierSalesView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetCashierSalesUseCase(DjangoCashierSalesQuery()).execute(
            dates.date_from, dates.date_to
        )
        return Response(CashierSalesSerializer(data, many=True).data)


class CashierSalesCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetCashierSalesUseCase(DjangoCashierSalesQuery()).execute(
            dates.date_from, dates.date_to
        )
        return _csv_response(write_cashier_sales_csv(data), "cashier_sales.csv")


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


class ProfitReportCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        dates = DateRange.from_params(request.query_params)
        data = GetProfitReportUseCase(DjangoProfitReportQuery()).execute(
            dates.date_from, dates.date_to
        )
        return _csv_response(write_profit_report_csv(data), "profit_report.csv")


class InventoryReportView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        report = GetInventoryReportUseCase(DjangoInventoryReportQuery()).execute()
        return Response(InventoryReportSerializer(report).data)


class LowStockCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        items = GetLowStockItemsUseCase(DjangoLowStockQuery()).execute()
        return _csv_response(write_low_stock_csv(items), "low_stock.csv")


class InventoryReportCSVView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        report = GetInventoryReportUseCase(DjangoInventoryReportQuery()).execute()
        return _csv_response(write_inventory_report_csv(report), "inventory_report.csv")


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

        response = HttpResponse(write_sales_report_csv(rows), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=sales_report.csv"
        return response

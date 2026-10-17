from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from reporting.application.use_cases import (
    GetCashierSalesUseCase,
    GetDailySalesUseCase,
    GetSalesByPaymentMethodUseCase,
    GetSalesSummaryUseCase,
    GetTopProductsUseCase,
)
from reporting.infrastructure.query_builders import SalesQueryBuilder
from reporting.interfaces.api.serializers import (
    CashierSalesSerializer,
    DailySalesSerializer,
    SalesByPaymentMethodSerializer,
    SalesSummarySerializer,
    TopProductSerializer,
)


class SalesSummaryView(APIView):
    def get(self, request):
        date_from = date.fromisoformat(request.query_params.get("date_from", "2026-01-01"))
        date_to = date.fromisoformat(request.query_params.get("date_to", "2026-12-31"))
        use_case = GetSalesSummaryUseCase(SalesQueryBuilder())
        summary = use_case.execute(date_from, date_to)
        return Response(SalesSummarySerializer(summary).data)


class TopProductsView(APIView):
    def get(self, request):
        date_from = date.fromisoformat(request.query_params.get("date_from", "2026-01-01"))
        date_to = date.fromisoformat(request.query_params.get("date_to", "2026-12-31"))
        limit = int(request.query_params.get("limit", 10))
        use_case = GetTopProductsUseCase(SalesQueryBuilder())
        products = use_case.execute(date_from, date_to, limit)
        return Response(TopProductSerializer(products, many=True).data)


class SalesByPaymentMethodView(APIView):
    def get(self, request):
        date_from = date.fromisoformat(request.query_params.get("date_from", "2026-01-01"))
        date_to = date.fromisoformat(request.query_params.get("date_to", "2026-12-31"))
        use_case = GetSalesByPaymentMethodUseCase(SalesQueryBuilder())
        data = use_case.execute(date_from, date_to)
        return Response(SalesByPaymentMethodSerializer(data, many=True).data)


class DailySalesView(APIView):
    def get(self, request):
        date_from = date.fromisoformat(request.query_params.get("date_from", "2026-01-01"))
        date_to = date.fromisoformat(request.query_params.get("date_to", "2026-12-31"))
        use_case = GetDailySalesUseCase(SalesQueryBuilder())
        data = use_case.execute(date_from, date_to)
        return Response(DailySalesSerializer(data, many=True).data)


class CashierSalesView(APIView):
    def get(self, request):
        date_from = date.fromisoformat(request.query_params.get("date_from", "2026-01-01"))
        date_to = date.fromisoformat(request.query_params.get("date_to", "2026-12-31"))
        use_case = GetCashierSalesUseCase(SalesQueryBuilder())
        data = use_case.execute(date_from, date_to)
        return Response(CashierSalesSerializer(data, many=True).data)

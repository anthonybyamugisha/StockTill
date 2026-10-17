from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.clock import SystemClock
from shared.domain.money import Money
from shared.infrastructure.audit import build_audit_recorder
from shifts.application.commands import (
    CloseShiftCommand,
    OpenShiftCommand,
    RecordCashMovementCommand,
)
from shifts.application.ports import CashTotals
from shifts.application.use_cases import (
    CloseShiftUseCase,
    GetCurrentShiftUseCase,
    GetShiftReportUseCase,
    OpenShiftUseCase,
    RecordCashMovementUseCase,
)
from shifts.domain.entities import CashMovementType, Shift
from shifts.domain.errors import ShiftError
from shifts.infrastructure.adapters import SalesSummaryAdapter
from shifts.infrastructure.repository import (
    DjangoCashMovementRepository,
    DjangoShiftRepository,
)
from shifts.interfaces.api.serializers import (
    CashMovementInputSerializer,
    CashMovementSerializer,
    CloseShiftSerializer,
    OpenShiftSerializer,
    ShiftSerializer,
)


def _report_payload(shift: Shift, totals: CashTotals) -> dict:
    expected = shift.expected_cash(totals.sales, totals.refunds)
    variance = shift.variance(totals.sales, totals.refunds)
    return {
        "shift": ShiftSerializer(shift).data,
        "cash_sales": totals.sales.amount,
        "cash_refunds": totals.refunds.amount,
        "net_cash_movements": shift.net_cash_movements().amount,
        "expected_cash": expected.amount,
        "counted_cash": shift.counted_cash.amount if shift.counted_cash else None,
        "variance": variance.amount if variance is not None else None,
    }


class CurrentShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shift = GetCurrentShiftUseCase(
            DjangoShiftRepository(), DjangoCashMovementRepository()
        ).execute(request.user.id)
        return Response({"shift": ShiftSerializer(shift).data if shift else None})


class OpenShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OpenShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = OpenShiftUseCase(DjangoShiftRepository(), SystemClock(), build_audit_recorder())
        try:
            shift = use_case.execute(
                OpenShiftCommand(
                    cashier_id=request.user.id,
                    opening_float=Money(data["opening_float"]),
                    notes=data.get("notes", ""),
                )
            )
        except ShiftError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ShiftSerializer(shift).data, status=status.HTTP_201_CREATED)


class CloseShiftView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CloseShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = CloseShiftUseCase(
            DjangoShiftRepository(),
            DjangoCashMovementRepository(),
            SalesSummaryAdapter(),
            SystemClock(),
            build_audit_recorder(),
        )
        try:
            shift, totals = use_case.execute(
                CloseShiftCommand(
                    shift_id=data["shift_id"],
                    counted_cash=Money(data["counted_cash"]),
                    notes=data.get("notes", ""),
                    user_id=request.user.id,
                )
            )
        except ShiftError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_report_payload(shift, totals))


class ShiftReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, shift_id):
        use_case = GetShiftReportUseCase(
            DjangoShiftRepository(), DjangoCashMovementRepository(), SalesSummaryAdapter()
        )
        try:
            shift, totals = use_case.execute(shift_id)
        except ShiftError as error:
            return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
        return Response(_report_payload(shift, totals))


class CashMovementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CashMovementInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = RecordCashMovementUseCase(
            DjangoShiftRepository(),
            DjangoCashMovementRepository(),
            SystemClock(),
            build_audit_recorder(),
        )
        try:
            movement = use_case.execute(
                RecordCashMovementCommand(
                    shift_id=data["shift_id"],
                    type=CashMovementType(data["type"]),
                    amount=Money(data["amount"]),
                    reason=data.get("reason", ""),
                    user_id=request.user.id,
                )
            )
        except ShiftError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CashMovementSerializer(movement).data, status=status.HTTP_201_CREATED)

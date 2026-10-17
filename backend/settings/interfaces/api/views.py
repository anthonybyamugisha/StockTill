from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsAdmin
from settings.application.use_cases import GetSettingsUseCase, UpdateSettingsUseCase
from settings.infrastructure.repository import DjangoSettingsRepository
from settings.interfaces.api.serializers import SettingsSerializer
from shared.infrastructure.audit import build_audit_recorder


class SettingsView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        use_case = GetSettingsUseCase(DjangoSettingsRepository())
        settings = use_case.execute()
        return Response(SettingsSerializer(settings).data)

    def put(self, request):
        serializer = SettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from shared.domain.settings import BusinessSettings

        settings = BusinessSettings(**serializer.validated_data)
        use_case = UpdateSettingsUseCase(DjangoSettingsRepository(), build_audit_recorder())
        updated = use_case.execute(
            settings, actor_id=request.user.id if request.user.is_authenticated else None
        )
        return Response(SettingsSerializer(updated).data)

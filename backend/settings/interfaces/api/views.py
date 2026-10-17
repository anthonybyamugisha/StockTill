from rest_framework.response import Response
from rest_framework.views import APIView

from settings.application.use_cases import GetSettingsUseCase, UpdateSettingsUseCase
from settings.infrastructure.repository import DjangoSettingsRepository
from settings.interfaces.api.serializers import SettingsSerializer


class SettingsView(APIView):
    def get(self, request):
        use_case = GetSettingsUseCase(DjangoSettingsRepository())
        settings = use_case.execute()
        return Response(SettingsSerializer(settings).data)

    def put(self, request):
        serializer = SettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from shared.domain.settings import BusinessSettings

        settings = BusinessSettings(**serializer.validated_data)
        use_case = UpdateSettingsUseCase(DjangoSettingsRepository())
        updated = use_case.execute(settings)
        return Response(SettingsSerializer(updated).data)

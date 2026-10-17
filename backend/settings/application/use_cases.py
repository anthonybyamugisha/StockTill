from settings.domain.repository import SettingsRepository
from shared.domain.settings import BusinessSettings


class GetSettingsUseCase:
    def __init__(self, repository: SettingsRepository):
        self._repo = repository

    def execute(self) -> BusinessSettings:
        return self._repo.get()


class UpdateSettingsUseCase:
    def __init__(self, repository: SettingsRepository):
        self._repo = repository

    def execute(self, settings: BusinessSettings) -> BusinessSettings:
        self._repo.save(settings)
        return settings

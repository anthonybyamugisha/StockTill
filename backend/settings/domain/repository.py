from abc import ABC, abstractmethod

from shared.domain.settings import BusinessSettings


class SettingsRepository(ABC):
    @abstractmethod
    def get(self) -> BusinessSettings:
        pass

    @abstractmethod
    def save(self, settings: BusinessSettings) -> None:
        pass

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from django.utils import timezone


@dataclass(frozen=True)
class DateRange:
    date_from: date
    date_to: date

    @classmethod
    def from_params(cls, params: Mapping[str, str]) -> "DateRange":
        today = timezone.localdate()
        return cls(
            date_from=_parse(params.get("date_from"), today.replace(day=1)),
            date_to=_parse(params.get("date_to"), today),
        )


def _parse(raw: str | None, default: date) -> date:
    if not raw:
        return default
    return date.fromisoformat(raw)

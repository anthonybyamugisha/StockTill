from datetime import date

from reporting.interfaces.api.date_range import DateRange


def _freeze_shop_today(monkeypatch, today: date) -> None:
    monkeypatch.setattr("reporting.interfaces.api.date_range.timezone.localdate", lambda: today)


def test_defaults_to_the_month_to_date(monkeypatch):
    _freeze_shop_today(monkeypatch, date(2026, 10, 18))

    dates = DateRange.from_params({})

    assert dates == DateRange(date_from=date(2026, 10, 1), date_to=date(2026, 10, 18))


def test_uses_explicit_bounds(monkeypatch):
    _freeze_shop_today(monkeypatch, date(2026, 10, 18))

    dates = DateRange.from_params({"date_from": "2026-09-01", "date_to": "2026-09-30"})

    assert dates == DateRange(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))


def test_fills_only_the_missing_bound(monkeypatch):
    _freeze_shop_today(monkeypatch, date(2026, 10, 18))

    dates = DateRange.from_params({"date_from": "2026-10-10"})

    assert dates == DateRange(date_from=date(2026, 10, 10), date_to=date(2026, 10, 18))


def test_blank_values_fall_back_to_defaults(monkeypatch):
    _freeze_shop_today(monkeypatch, date(2026, 2, 3))

    dates = DateRange.from_params({"date_from": "", "date_to": ""})

    assert dates == DateRange(date_from=date(2026, 2, 1), date_to=date(2026, 2, 3))

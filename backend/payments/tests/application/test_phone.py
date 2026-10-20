import pytest

from payments.application.phone import normalize_phone


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0772123456", "256772123456"),
        ("+256772123456", "256772123456"),
        ("256772123456", "256772123456"),
        ("772123456", "256772123456"),
        ("00256772123456", "256772123456"),
        ("0772 123 456", "256772123456"),
        ("(0772) 123-456", "256772123456"),
        ("0759123456", "256759123456"),
    ],
)
def test_normalises_ugandan_numbers_to_the_country_code(raw, expected):
    assert normalize_phone(raw) == expected


def test_leaves_an_unrecognised_number_untouched():
    assert normalize_phone("12345") == "12345"


def test_an_empty_number_stays_empty():
    assert normalize_phone("") == ""

import pytest

from sales.domain.entities import SaleStatus
from sales.interfaces.api.filters import parse_status_filter


def test_no_status_means_no_filter():
    assert parse_status_filter(None) is None
    assert parse_status_filter("") is None


def test_reads_a_known_status():
    assert parse_status_filter("partially_refunded") == SaleStatus.PARTIALLY_REFUNDED


def test_names_the_bad_value_in_the_error():
    with pytest.raises(ValueError, match="'refunded_twice' is not a valid sale status"):
        parse_status_filter("refunded_twice")

from sales.domain.entities import SaleStatus


def parse_status_filter(value: str | None) -> SaleStatus | None:
    if not value:
        return None
    try:
        return SaleStatus(value)
    except ValueError:
        raise ValueError(f"'{value}' is not a valid sale status.") from None

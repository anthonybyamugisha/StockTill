import re


def normalize_phone(raw: str, *, country_code: str = "256") -> str:
    """Turn a locally written number into the MSISDN the networks expect."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith(country_code):
        return digits
    if digits.startswith("0"):
        return f"{country_code}{digits[1:]}"
    if len(digits) == 9:
        return f"{country_code}{digits}"
    return digits

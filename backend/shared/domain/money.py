from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
CENT = Decimal("0.01")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "UGX"

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", self.amount.quantize(CENT, rounding=ROUND_HALF_UP))

    @classmethod
    def zero(cls, currency: str = "UGX") -> "Money":
        return cls(ZERO, currency)

    def add(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: Decimal) -> "Money":
        return Money(self.amount * factor, self.currency)

    def is_zero(self) -> bool:
        return self.amount == ZERO

    def is_negative(self) -> bool:
        return self.amount < ZERO

    def __str__(self) -> str:
        return str(self.amount)

    def __add__(self, other: "Money") -> "Money":
        return self.add(other)

    def __sub__(self, other: "Money") -> "Money":
        return self.subtract(other)

    def __lt__(self, other: "Money") -> bool:
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        return self.amount >= other.amount

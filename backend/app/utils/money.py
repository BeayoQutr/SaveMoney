from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def round_money(value: float | int | str | Decimal) -> float:
    return float(Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP))


def sum_money(values: list[float | int | str | Decimal]) -> float:
    total = sum((Decimal(str(value)) for value in values), Decimal("0.00"))
    return round_money(total)


def to_cents(yuan: float) -> int:
    """Convert yuan (元) to cents (分) using banker's rounding."""
    return int(Decimal(str(yuan)).quantize(CENT, rounding=ROUND_HALF_UP) * 100)


def from_cents(cents: int) -> float:
    """Convert cents (分) to yuan (元)."""
    return float(Decimal(cents) / 100)

from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def round_money(value: float | int | str | Decimal) -> float:
    return float(Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP))


def sum_money(values: list[float | int | str | Decimal]) -> float:
    total = sum((Decimal(str(value)) for value in values), Decimal("0.00"))
    return round_money(total)

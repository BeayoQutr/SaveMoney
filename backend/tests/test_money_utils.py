import unittest

from app.utils.money import from_cents, round_money, sum_money, to_cents


class MoneyUtilsTest(unittest.TestCase):
    def test_money_helpers_use_decimal_half_up_rounding(self) -> None:
        self.assertEqual(round_money(1.005), 1.01)
        self.assertEqual(sum_money([0.1, 0.2]), 0.3)
        self.assertEqual(to_cents(12.345), 1235)
        self.assertEqual(from_cents(1235), 12.35)


if __name__ == "__main__":
    unittest.main()

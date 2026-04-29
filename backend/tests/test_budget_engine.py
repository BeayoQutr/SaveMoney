from datetime import date, timedelta
import unittest

from app.budget_engine import adjust_saving_plan, generate_saving_plan
from app.schemas import AdjustPlanRequest, GeneratePlanRequest


class BudgetEngineTest(unittest.TestCase):
    def test_deadline_in_past_is_invalid(self) -> None:
        result = generate_saving_plan(
            GeneratePlanRequest(
                monthly_income=3000,
                fixed_expenses=1000,
                target_amount=1000,
                deadline=date.today() - timedelta(days=1),
                identity="student",
                minimum_living_cost=500,
            )
        )

        self.assertEqual(result.status, "invalid")
        self.assertEqual(result.feasibility_score, 0)

    def test_deadline_today_is_invalid(self) -> None:
        result = generate_saving_plan(
            GeneratePlanRequest(
                monthly_income=3000,
                fixed_expenses=1000,
                target_amount=1000,
                deadline=date.today(),
                identity="student",
                minimum_living_cost=500,
            )
        )

        self.assertEqual(result.status, "invalid")

    def test_fixed_expenses_greater_than_income_is_impossible(self) -> None:
        result = generate_saving_plan(
            GeneratePlanRequest(
                monthly_income=1000,
                fixed_expenses=1200,
                target_amount=1000,
                deadline=date.today() + timedelta(days=30),
                identity="worker",
                minimum_living_cost=300,
            )
        )

        self.assertEqual(result.status, "impossible")

    def test_minimum_living_cost_too_high_is_impossible(self) -> None:
        result = generate_saving_plan(
            GeneratePlanRequest(
                monthly_income=3000,
                fixed_expenses=1000,
                target_amount=1000,
                deadline=date.today() + timedelta(days=30),
                identity="student",
                minimum_living_cost=2500,
            )
        )

        self.assertEqual(result.status, "impossible")

    def test_feasible_goal_returns_ok(self) -> None:
        result = generate_saving_plan(
            GeneratePlanRequest(
                monthly_income=5000,
                fixed_expenses=1000,
                target_amount=1000,
                deadline=date.today() + timedelta(days=30),
                identity="worker",
                minimum_living_cost=1000,
            )
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.feasibility_score, 100)

    def test_hard_goal_returns_hard(self) -> None:
        result = generate_saving_plan(
            GeneratePlanRequest(
                monthly_income=3000,
                fixed_expenses=1000,
                target_amount=6000,
                deadline=date.today() + timedelta(days=30),
                identity="worker",
                minimum_living_cost=1000,
            )
        )

        self.assertEqual(result.status, "hard")
        self.assertLess(result.feasibility_score, 100)

    def test_adjust_plan(self) -> None:
        result = adjust_saving_plan(
            AdjustPlanRequest(
                target_amount=1000,
                saved_amount=200,
                remaining_days=20,
                planned_daily_saving=40,
                actual_expense_today=80,
                daily_available=100,
            )
        )

        self.assertEqual(result.remaining_amount, 800)
        self.assertEqual(result.today_gap, 20)
        self.assertEqual(result.new_daily_saving, 41)

    def test_adjust_plan_target_already_reached(self) -> None:
        result = adjust_saving_plan(
            AdjustPlanRequest(
                target_amount=1000,
                saved_amount=1200,
                remaining_days=20,
                planned_daily_saving=40,
                actual_expense_today=0,
                daily_available=100,
            )
        )

        self.assertEqual(result.remaining_amount, 0)
        self.assertEqual(result.new_daily_saving, 0)
        self.assertEqual(result.status, "ok")


if __name__ == "__main__":
    unittest.main()

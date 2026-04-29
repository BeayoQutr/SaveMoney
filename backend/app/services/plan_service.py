"""Service layer for saving plans persistence."""

from datetime import date

from sqlalchemy.orm import Session

from app.models import SavingPlan
from app.schemas import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    SavingPlanCurrentResponse,
    SavingPlanItemResponse,
)
from app.budget_engine import generate_saving_plan
from app.utils.money import from_cents, round_money, to_cents


def _money_from_plan(plan: SavingPlan, yuan_attr: str, cents_attr: str) -> float:
    cents = getattr(plan, cents_attr)
    if cents is not None:
        return from_cents(cents)
    return round_money(getattr(plan, yuan_attr))


def _plan_response(plan: SavingPlan) -> SavingPlanItemResponse:
    return SavingPlanItemResponse(
        id=plan.id,
        target_amount=_money_from_plan(plan, "target_amount", "target_amount_cents"),
        deadline=plan.deadline,
        monthly_income=_money_from_plan(plan, "monthly_income", "monthly_income_cents"),
        fixed_expenses=_money_from_plan(plan, "fixed_expenses", "fixed_expenses_cents"),
        minimum_living_cost=_money_from_plan(
            plan,
            "minimum_living_cost",
            "minimum_living_cost_cents",
        ),
        identity=plan.identity,
        saved_amount=_money_from_plan(plan, "saved_amount", "saved_amount_cents"),
        status=plan.status,
    )


def generate_and_save_plan(db: Session, data: GeneratePlanRequest) -> SavingPlanItemResponse:
    """Generate a saving plan and persist it to the database."""
    target_amount = round_money(data.target_amount)
    monthly_income = round_money(data.monthly_income)
    fixed_expenses = round_money(data.fixed_expenses)
    minimum_living_cost = round_money(data.minimum_living_cost)
    plan = SavingPlan(
        target_amount=target_amount,
        target_amount_cents=to_cents(target_amount),
        deadline=data.deadline,
        monthly_income=monthly_income,
        monthly_income_cents=to_cents(monthly_income),
        fixed_expenses=fixed_expenses,
        fixed_expenses_cents=to_cents(fixed_expenses),
        minimum_living_cost=minimum_living_cost,
        minimum_living_cost_cents=to_cents(minimum_living_cost),
        identity=data.identity,
        saved_amount=0.0,
        saved_amount_cents=0,
        status="active",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_response(plan)


def get_current_plan(db: Session) -> SavingPlanCurrentResponse:
    """Return the most recent active saving plan with computed daily metrics."""
    plan = (
        db.query(SavingPlan)
        .filter(SavingPlan.status == "active")
        .order_by(SavingPlan.id.desc())
        .first()
    )
    if plan is None:
        return SavingPlanCurrentResponse(plan=None)

    today = date.today()
    remaining_days = (plan.deadline - today).days
    if remaining_days <= 0:
        remaining_days = 0

    target_amount = _money_from_plan(plan, "target_amount", "target_amount_cents")
    monthly_income = _money_from_plan(plan, "monthly_income", "monthly_income_cents")
    fixed_expenses = _money_from_plan(plan, "fixed_expenses", "fixed_expenses_cents")
    minimum_living_cost = _money_from_plan(
        plan,
        "minimum_living_cost",
        "minimum_living_cost_cents",
    )
    saved_amount = _money_from_plan(plan, "saved_amount", "saved_amount_cents")

    remaining_amount = max(target_amount - saved_amount, 0)
    daily_saving = round_money(remaining_amount / remaining_days) if remaining_days > 0 else 0.0

    monthly_available = monthly_income - fixed_expenses
    safe_capacity = monthly_available - minimum_living_cost
    daily_available = round_money(safe_capacity / 30) if safe_capacity > 0 else 0.0

    return SavingPlanCurrentResponse(
        plan=_plan_response(plan),
        daily_saving=daily_saving,
        daily_available=daily_available,
        remaining_days=remaining_days,
    )


def update_saved_amount(db: Session, plan_id: int, saved_amount: float) -> SavingPlanItemResponse:
    """Update the saved_amount for a plan."""
    plan = db.query(SavingPlan).filter(SavingPlan.id == plan_id).first()
    if plan is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="攒钱计划不存在")

    saved_amount = round_money(saved_amount)
    plan.saved_amount = saved_amount
    plan.saved_amount_cents = to_cents(saved_amount)
    target_amount = _money_from_plan(plan, "target_amount", "target_amount_cents")
    if saved_amount >= target_amount:
        plan.status = "completed"
    db.commit()
    db.refresh(plan)
    return _plan_response(plan)

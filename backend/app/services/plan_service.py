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


def generate_and_save_plan(db: Session, data: GeneratePlanRequest) -> SavingPlanItemResponse:
    """Generate a saving plan and persist it to the database."""
    plan = SavingPlan(
        target_amount=data.target_amount,
        deadline=data.deadline,
        monthly_income=data.monthly_income,
        fixed_expenses=data.fixed_expenses,
        minimum_living_cost=data.minimum_living_cost,
        identity=data.identity,
        saved_amount=0.0,
        status="active",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return SavingPlanItemResponse.model_validate(plan)


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

    remaining_amount = max(plan.target_amount - plan.saved_amount, 0)
    daily_saving = round(remaining_amount / remaining_days, 2) if remaining_days > 0 else 0.0

    monthly_available = plan.monthly_income - plan.fixed_expenses
    safe_capacity = monthly_available - plan.minimum_living_cost
    daily_available = round(safe_capacity / 30, 2) if safe_capacity > 0 else 0.0

    return SavingPlanCurrentResponse(
        plan=SavingPlanItemResponse.model_validate(plan),
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

    plan.saved_amount = saved_amount
    if saved_amount >= plan.target_amount:
        plan.status = "completed"
    db.commit()
    db.refresh(plan)
    return SavingPlanItemResponse.model_validate(plan)
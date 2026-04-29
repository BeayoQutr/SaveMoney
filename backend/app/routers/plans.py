from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.budget_engine import adjust_saving_plan, generate_saving_plan
from app.database import get_db
from app.schemas import (
    AdjustPlanRequest,
    AdjustPlanResponse,
    GeneratePlanRequest,
    GeneratePlanResponse,
    SavingPlanCurrentResponse,
    SavingPlanItemResponse,
    SavingPlanUpdateRequest,
)
from app.services import plan_service


router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/generate", response_model=GeneratePlanResponse)
def generate_plan(data: GeneratePlanRequest, db: Session = Depends(get_db)):
    # Persist the plan
    plan_service.generate_and_save_plan(db, data)
    return generate_saving_plan(data)


@router.post("/adjust", response_model=AdjustPlanResponse)
def adjust_plan(data: AdjustPlanRequest):
    return adjust_saving_plan(data)


@router.get("/current", response_model=SavingPlanCurrentResponse)
def get_current_plan(db: Session = Depends(get_db)):
    return plan_service.get_current_plan(db)


@router.put("/{plan_id}", response_model=SavingPlanItemResponse)
def update_plan(plan_id: int, data: SavingPlanUpdateRequest, db: Session = Depends(get_db)):
    return plan_service.update_saved_amount(db, plan_id, data.saved_amount)
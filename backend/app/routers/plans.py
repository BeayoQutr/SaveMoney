from fastapi import APIRouter

from app.budget_engine import adjust_saving_plan, generate_saving_plan
from app.schemas import (
    AdjustPlanRequest,
    AdjustPlanResponse,
    GeneratePlanRequest,
    GeneratePlanResponse,
)


router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/generate", response_model=GeneratePlanResponse)
def generate_plan(data: GeneratePlanRequest):
    return generate_saving_plan(data)


@router.post("/adjust", response_model=AdjustPlanResponse)
def adjust_plan(data: AdjustPlanRequest):
    return adjust_saving_plan(data)

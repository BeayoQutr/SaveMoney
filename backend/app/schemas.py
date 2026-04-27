from datetime import date
from pydantic import BaseModel, Field


class GeneratePlanRequest(BaseModel):
    monthly_income: float = Field(gt=0)
    fixed_expenses: float = Field(ge=0)
    target_amount: float = Field(gt=0)
    deadline: date


class GeneratePlanResponse(BaseModel):
    remaining_days: int
    daily_saving: float
    monthly_available: float
    status: str
    message: str
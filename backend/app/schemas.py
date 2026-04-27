from datetime import date
from pydantic import BaseModel, Field


class GeneratePlanRequest(BaseModel):
    monthly_income: float = Field(gt=0)
    fixed_expenses: float = Field(ge=0)
    target_amount: float = Field(gt=0)
    deadline: date
    identity: str
    minimum_living_cost: float = Field(ge=0)


class GeneratePlanResponse(BaseModel):
    remaining_days: int
    daily_saving: float
    monthly_available: float
    daily_available: float
    target_amount: float
    feasibility_score: int
    minimum_living_cost: float
    safe_saving_capacity: float
    status: str
    message: str


class ExpenseCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    note: str = Field(min_length=1)
    date: date


class ExpenseCreateResponse(BaseModel):
    amount: float
    note: str
    date: date
    category: str
    message: str

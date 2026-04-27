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
    id: int
    amount: float
    note: str
    date: date
    category: str
    message: str


class ExpenseItemResponse(BaseModel):
    id: int
    amount: float
    note: str
    date: date
    category: str


class DailyExpenseSummaryResponse(BaseModel):
    date: date
    total_amount: float
    count: int


class AdjustPlanRequest(BaseModel):
    target_amount: float = Field(gt=0)
    saved_amount: float = Field(ge=0)
    remaining_days: int = Field(gt=0)
    planned_daily_saving: float = Field(ge=0)
    actual_expense_today: float = Field(ge=0)
    daily_available: float = Field(ge=0)


class AdjustPlanResponse(BaseModel):
    remaining_amount: float
    today_gap: float
    new_daily_saving: float
    adjustment_per_day: float
    status: str
    message: str


class CategorySummaryItem(BaseModel):
    category: str
    total_amount: float
    count: int


class CategorySummaryResponse(BaseModel):
    start_date: date
    end_date: date
    items: list[CategorySummaryItem]


class MonthlyExpenseSummaryResponse(BaseModel):
    month: str
    total_amount: float
    count: int
    average_daily_amount: float
    items: list[CategorySummaryItem]


class ExpenseDeleteResponse(BaseModel):
    message: str
    deleted_id: int

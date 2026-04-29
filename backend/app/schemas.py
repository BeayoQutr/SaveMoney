from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    note: str = Field(min_length=1, max_length=100)
    date: date
    category: str | None = Field(default=None, max_length=20)

    @field_validator("note")
    @classmethod
    def strip_note(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("备注不能为空")
        return value

    @field_validator("category")
    @classmethod
    def strip_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExpenseCreateResponse(BaseModel):
    id: int
    amount: float
    note: str
    date: date
    category: str
    message: str


class ExpenseItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class AiMonthlyAdviceResponse(BaseModel):
    month: str
    advice: str


class ExpenseDeleteResponse(BaseModel):
    message: str
    deleted_id: int


class AiSuggestCategoryRequest(BaseModel):
    amount: float = Field(gt=0)
    note: str = Field(min_length=1, max_length=100)

    @field_validator("note")
    @classmethod
    def strip_note(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("备注不能为空")
        return value


class AiSuggestCategoryResponse(BaseModel):
    category: str
    reason: str


class AiOptimizeNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=100)

    @field_validator("note")
    @classmethod
    def strip_note(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("备注不能为空")
        return value


class AiOptimizeNoteResponse(BaseModel):
    optimized_note: str

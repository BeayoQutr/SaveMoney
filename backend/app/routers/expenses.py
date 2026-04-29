from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CategorySummaryResponse,
    DailyExpenseSummaryResponse,
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseDeleteResponse,
    ExpenseItemResponse,
    ExpenseListResponse,
    MonthlyExpenseSummaryResponse,
)
from app.services import expense_service
from app.utils.csv_utils import build_expenses_csv_response


router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    keyword: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return expense_service.list_expenses(
        db,
        start_date=start_date,
        end_date=end_date,
        category=category,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ExpenseCreateResponse)
def create_expense(data: ExpenseCreateRequest, db: Session = Depends(get_db)):
    return expense_service.create_expense(db, data)


@router.put("/{expense_id}", response_model=ExpenseCreateResponse)
def update_expense(
    expense_id: int,
    data: ExpenseCreateRequest,
    db: Session = Depends(get_db),
):
    return expense_service.update_expense(db, expense_id, data)


@router.delete("/{expense_id}", response_model=ExpenseDeleteResponse)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    return expense_service.delete_expense(db, expense_id)


@router.get("/summary/daily", response_model=DailyExpenseSummaryResponse)
def daily_expense_summary(query_date: date, db: Session = Depends(get_db)):
    return expense_service.daily_summary(db, query_date)


@router.get("/summary/category", response_model=CategorySummaryResponse)
def expenses_summary_category(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    return expense_service.category_summary(db, start_date, end_date)


@router.get("/summary/monthly", response_model=MonthlyExpenseSummaryResponse)
def expenses_summary_monthly(month: str, db: Session = Depends(get_db)):
    return expense_service.monthly_summary(db, month)


@router.get("/export/csv")
def export_expenses_csv(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
) -> Response:
    rows = expense_service.expenses_for_export(db, start_date, end_date)
    return build_expenses_csv_response(rows, start_date, end_date)

import calendar

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from datetime import date, datetime
from typing import List

from sqlalchemy import func

from app.schemas import GeneratePlanRequest, GeneratePlanResponse
from app.schemas import (
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseItemResponse,
    DailyExpenseSummaryResponse,
    AdjustPlanRequest,
    AdjustPlanResponse,
    CategorySummaryItem,
    CategorySummaryResponse,
    MonthlyExpenseSummaryResponse,
    ExpenseDeleteResponse,
)
from app.budget_engine import generate_saving_plan, adjust_saving_plan
from app.database import engine, SessionLocal, Base
from app.models import Expense

app = FastAPI(title="SaveMoney API")

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "SaveMoney backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/plans/generate", response_model=GeneratePlanResponse)
def generate_plan(data: GeneratePlanRequest):
    return generate_saving_plan(data)


@app.post("/plans/adjust", response_model=AdjustPlanResponse)
def adjust_plan(data: AdjustPlanRequest):
    return adjust_saving_plan(data)


def classify_expense(note: str) -> str:
    if any(kw in note for kw in ["饭", "早餐", "午餐", "晚餐", "外卖"]):
        return "餐饮"
    if any(kw in note for kw in ["车", "公交", "地铁", "打车"]):
        return "交通"
    if any(kw in note for kw in ["书", "课程", "学习"]):
        return "学习"
    if any(kw in note for kw in ["药", "医院"]):
        return "医疗"
    return "其他"


@app.get("/expenses/summary/daily", response_model=DailyExpenseSummaryResponse)
def daily_expense_summary(query_date: date, db: Session = Depends(get_db)):
    result = (
        db.query(
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .filter(Expense.date == query_date)
        .first()
    )
    total = round(float(result[0]), 2)
    count = int(result[1])
    return DailyExpenseSummaryResponse(
        date=query_date,
        total_amount=total,
        count=count,
    )


@app.get("/expenses", response_model=List[ExpenseItemResponse])
def list_expenses(db: Session = Depends(get_db)):
    expenses = (
        db.query(Expense)
        .order_by(Expense.id.desc())
        .limit(50)
        .all()
    )
    return expenses


@app.get("/expenses/summary/category", response_model=CategorySummaryResponse)
def expenses_summary_category(start_date: date, end_date: date, db: Session = Depends(get_db)):
    rows = (
        db.query(
            Expense.category,
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .group_by(Expense.category)
        .all()
    )

    items = [
        CategorySummaryItem(
            category=row[0],
            total_amount=round(float(row[1]), 2),
            count=int(row[2]),
        )
        for row in rows
    ]

    return CategorySummaryResponse(
        start_date=start_date,
        end_date=end_date,
        items=items,
    )


@app.get("/expenses/summary/monthly", response_model=MonthlyExpenseSummaryResponse)
def expenses_summary_monthly(month: str, db: Session = Depends(get_db)):
    try:
        parsed = datetime.strptime(month + "-01", "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="month 格式错误，应为 YYYY-MM")

    year = parsed.year
    month_int = parsed.month
    days_in_month = calendar.monthrange(year, month_int)[1]

    start_date = date(year, month_int, 1)
    end_date = date(year, month_int, days_in_month)

    overall = (
        db.query(
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .first()
    )
    total = round(float(overall[0]), 2)
    count = int(overall[1])
    average_daily = round(total / days_in_month, 2) if days_in_month > 0 else 0.0

    rows = (
        db.query(
            Expense.category,
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .group_by(Expense.category)
        .all()
    )

    items = [
        CategorySummaryItem(
            category=row[0],
            total_amount=round(float(row[1]), 2),
            count=int(row[2]),
        )
        for row in rows
    ]

    return MonthlyExpenseSummaryResponse(
        month=month,
        total_amount=total,
        count=count,
        average_daily_amount=average_daily,
        items=items,
    )


@app.post("/expenses", response_model=ExpenseCreateResponse)
def create_expense(data: ExpenseCreateRequest, db: Session = Depends(get_db)):
    category = classify_expense(data.note)
    expense = Expense(
        amount=data.amount,
        note=data.note,
        date=data.date,
        category=category,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return ExpenseCreateResponse(
        id=expense.id,
        amount=expense.amount,
        note=expense.note,
        date=expense.date,
        category=expense.category,
        message="消费记录成功"
    )


@app.delete("/expenses/{expense_id}", response_model=ExpenseDeleteResponse)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if expense is None:
        raise HTTPException(status_code=404, detail="消费记录不存在")

    db.delete(expense)
    db.commit()

    return ExpenseDeleteResponse(
        message="消费记录删除成功",
        deleted_id=expense_id,
    )


@app.put("/expenses/{expense_id}", response_model=ExpenseCreateResponse)
def update_expense(expense_id: int, data: ExpenseCreateRequest, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if expense is None:
        raise HTTPException(status_code=404, detail="消费记录不存在")

    expense.amount = data.amount
    expense.note = data.note
    expense.date = data.date
    expense.category = classify_expense(data.note)

    db.commit()
    db.refresh(expense)

    return ExpenseCreateResponse(
        id=expense.id,
        amount=expense.amount,
        note=expense.note,
        date=expense.date,
        category=expense.category,
        message="消费记录更新成功",
    )

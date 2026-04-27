from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from datetime import date
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

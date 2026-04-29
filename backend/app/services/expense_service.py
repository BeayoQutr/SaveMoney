import calendar
from collections import defaultdict
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Expense
from app.schemas import (
    CategorySummaryItem,
    CategorySummaryResponse,
    DailyExpenseSummaryResponse,
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseDeleteResponse,
    MonthlyExpenseSummaryResponse,
)
from app.utils.date_utils import parse_month, validate_date_range
from app.utils.money import round_money, sum_money


AI_ALLOWED_CATEGORIES = [
    "餐饮",
    "交通",
    "学习",
    "娱乐",
    "购物",
    "医疗",
    "生活",
    "其他",
]


def classify_expense(note: str) -> str:
    if any(kw in note for kw in ["饭", "早餐", "午餐", "晚餐", "外卖"]):
        return "餐饮"
    if any(kw in note for kw in ["车", "公交", "地铁", "打车"]):
        return "交通"
    if any(kw in note for kw in ["书", "课程", "学习"]):
        return "学习"
    if any(kw in note for kw in ["药", "医院"]):
        return "医疗"
    if any(kw in note for kw in ["电影", "游戏", "KTV", "娱乐"]):
        return "娱乐"
    if any(kw in note for kw in ["买", "购物", "衣服", "鞋"]):
        return "购物"
    return "其他"


def normalize_expense_category(category: str | None, note: str) -> str:
    if category and category in AI_ALLOWED_CATEGORIES:
        return category
    return classify_expense(note)


def list_expenses(db: Session, limit: int = 50) -> list[Expense]:
    return db.query(Expense).order_by(Expense.id.desc()).limit(limit).all()


def create_expense(db: Session, data: ExpenseCreateRequest) -> ExpenseCreateResponse:
    expense = Expense(
        amount=round_money(data.amount),
        note=data.note,
        date=data.date,
        category=normalize_expense_category(data.category, data.note),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return ExpenseCreateResponse(
        id=expense.id,
        amount=round_money(expense.amount),
        note=expense.note,
        date=expense.date,
        category=expense.category,
        message="消费记录成功",
    )


def update_expense(
    db: Session,
    expense_id: int,
    data: ExpenseCreateRequest,
) -> ExpenseCreateResponse:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="消费记录不存在")

    expense.amount = round_money(data.amount)
    expense.note = data.note
    expense.date = data.date
    expense.category = normalize_expense_category(data.category, data.note)

    db.commit()
    db.refresh(expense)

    return ExpenseCreateResponse(
        id=expense.id,
        amount=round_money(expense.amount),
        note=expense.note,
        date=expense.date,
        category=expense.category,
        message="消费记录更新成功",
    )


def delete_expense(db: Session, expense_id: int) -> ExpenseDeleteResponse:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="消费记录不存在")

    db.delete(expense)
    db.commit()
    return ExpenseDeleteResponse(message="消费记录删除成功", deleted_id=expense_id)


def daily_summary(db: Session, query_date: date) -> DailyExpenseSummaryResponse:
    rows = db.query(Expense).filter(Expense.date == query_date).all()
    return DailyExpenseSummaryResponse(
        date=query_date,
        total_amount=sum_money([row.amount for row in rows]),
        count=len(rows),
    )


def category_summary(
    db: Session,
    start_date: date,
    end_date: date,
) -> CategorySummaryResponse:
    validate_date_range(start_date, end_date)
    rows = (
        db.query(Expense)
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .all()
    )

    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        buckets[row.category].append(row.amount)

    items = [
        CategorySummaryItem(
            category=category,
            total_amount=sum_money(amounts),
            count=len(amounts),
        )
        for category, amounts in buckets.items()
    ]
    items.sort(key=lambda item: item.total_amount, reverse=True)

    return CategorySummaryResponse(start_date=start_date, end_date=end_date, items=items)


def monthly_summary(db: Session, month: str) -> MonthlyExpenseSummaryResponse:
    start_date, end_date = parse_month(month)
    days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
    summary = category_summary(db, start_date, end_date)
    total = sum_money([item.total_amount for item in summary.items])
    count = sum(item.count for item in summary.items)
    average_daily = round_money(total / days_in_month) if days_in_month > 0 else 0.0

    return MonthlyExpenseSummaryResponse(
        month=month,
        total_amount=total,
        count=count,
        average_daily_amount=average_daily,
        items=summary.items,
    )


def expenses_for_export(db: Session, start_date: date, end_date: date) -> list[Expense]:
    validate_date_range(start_date, end_date)
    return (
        db.query(Expense)
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .order_by(Expense.date.asc(), Expense.id.asc())
        .all()
    )

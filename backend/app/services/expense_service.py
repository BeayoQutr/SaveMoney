import calendar
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Expense
from app.schemas import (
    CategorySummaryItem,
    CategorySummaryResponse,
    DailyExpenseSummaryResponse,
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseDeleteResponse,
    ExpenseListResponse,
    MonthlyExpenseSummaryResponse,
)
from app.utils.date_utils import parse_month, validate_date_range
from app.utils.money import from_cents, round_money, to_cents


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


def list_expenses(
    db: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    keyword: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ExpenseListResponse:
    if start_date is not None and end_date is not None:
        validate_date_range(start_date, end_date)

    query = db.query(Expense)
    if start_date is not None:
        query = query.filter(Expense.date >= start_date)
    if end_date is not None:
        query = query.filter(Expense.date <= end_date)
    if category is not None:
        query = query.filter(Expense.category == category)
    if keyword is not None:
        query = query.filter(Expense.note.contains(keyword))
    total = query.count()
    items = query.order_by(Expense.date.desc(), Expense.id.desc()).offset(offset).limit(limit).all()
    return ExpenseListResponse(items=items, total=total, limit=limit, offset=offset)


def create_expense(db: Session, data: ExpenseCreateRequest) -> ExpenseCreateResponse:
    amount_val = round_money(data.amount)
    expense = Expense(
        amount=amount_val,
        amount_cents=to_cents(amount_val),
        note=data.note,
        date=data.date,
        category=normalize_expense_category(data.category, data.note),
        payment_method=data.payment_method,
        is_necessary=data.is_necessary,
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
        payment_method=expense.payment_method,
        is_necessary=expense.is_necessary,
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

    amount_val = round_money(data.amount)
    expense.amount = amount_val
    expense.amount_cents = to_cents(amount_val)
    expense.note = data.note
    expense.date = data.date
    expense.category = normalize_expense_category(data.category, data.note)
    expense.payment_method = data.payment_method
    expense.is_necessary = data.is_necessary

    db.commit()
    db.refresh(expense)

    return ExpenseCreateResponse(
        id=expense.id,
        amount=round_money(expense.amount),
        note=expense.note,
        date=expense.date,
        category=expense.category,
        payment_method=expense.payment_method,
        is_necessary=expense.is_necessary,
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
    total_cents, count = (
        db.query(func.coalesce(func.sum(Expense.amount_cents), 0), func.count(Expense.id))
        .filter(Expense.date == query_date)
        .one()
    )
    return DailyExpenseSummaryResponse(
        date=query_date,
        total_amount=from_cents(int(total_cents or 0)),
        count=count,
    )


def category_summary(
    db: Session,
    start_date: date,
    end_date: date,
) -> CategorySummaryResponse:
    validate_date_range(start_date, end_date)
    rows = (
        db.query(
            Expense.category,
            func.coalesce(func.sum(Expense.amount_cents), 0).label("total_cents"),
            func.count(Expense.id).label("expense_count"),
        )
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .group_by(Expense.category)
        .all()
    )

    items = [
        CategorySummaryItem(
            category=row.category,
            total_amount=from_cents(int(row.total_cents or 0)),
            count=row.expense_count,
        )
        for row in rows
    ]
    items.sort(key=lambda item: item.total_amount, reverse=True)

    return CategorySummaryResponse(start_date=start_date, end_date=end_date, items=items)


def monthly_summary(db: Session, month: str) -> MonthlyExpenseSummaryResponse:
    start_date, end_date = parse_month(month)
    days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
    summary = category_summary(db, start_date, end_date)
    total = round_money(sum(item.total_amount for item in summary.items))
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

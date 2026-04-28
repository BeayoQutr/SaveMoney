import calendar
import csv
import io
import json

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from datetime import date, datetime
from typing import List

from sqlalchemy import func

from app.schemas import (
    AiMonthlyAdviceResponse,
    AiSuggestCategoryRequest,
    AiSuggestCategoryResponse,
    AiOptimizeNoteRequest,
    AiOptimizeNoteResponse,
)
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
from app.ai_client import call_deepseek
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


def normalize_expense_category(category: str | None, note: str) -> str:
    if category and category in AI_ALLOWED_CATEGORIES:
        return category
    return classify_expense(note)


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
    category = normalize_expense_category(data.category, data.note)
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
    expense.category = normalize_expense_category(data.category, data.note)

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


@app.get("/ai/monthly-advice", response_model=AiMonthlyAdviceResponse)
def ai_monthly_advice(month: str, db: Session = Depends(get_db)):
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

    if count == 0:
        return AiMonthlyAdviceResponse(
            month=month,
            advice="这个月还没有消费记录，暂时无法生成 AI 消费分析。你可以先记录几笔消费后再试。",
        )

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

    category_lines = "\n".join(
        f"- {row[0]}：{round(float(row[1]), 2)} 元（{int(row[2])} 笔）"
        for row in rows
    )

    system_prompt = (
        "你是一个个人攒钱和消费记录应用里的 AI 消费分析助手。"
        "你要基于用户提供的消费统计数据，给出理性、克制、可执行的中文建议。"
        "不要编造不存在的收入、目标金额或身体健康信息。"
        "不要使用夸张语气。"
        "不要输出医疗、投资、贷款建议。"
    )

    user_prompt = (
        f"月份：{month}\n"
        f"本月总消费：{total} 元\n"
        f"消费笔数：{count} 笔\n"
        f"日均消费：{average_daily} 元\n"
        f"分类统计：\n{category_lines}\n\n"
        "请先用 1 句话总结本月消费情况，再给 3 条具体建议。每条建议要短。不超过 300 字。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        advice = call_deepseek(messages, temperature=0.4, max_tokens=500)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后再试")

    return AiMonthlyAdviceResponse(month=month, advice=advice)


@app.get("/expenses/export/csv")
def export_expenses_csv(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Expense)
        .filter(Expense.date >= start_date, Expense.date <= end_date)
        .order_by(Expense.date.asc(), Expense.id.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "amount", "note", "date", "category"])
    for e in rows:
        writer.writerow([e.id, e.amount, e.note, e.date.isoformat(), e.category])

    filename = f"expenses_{start_date.isoformat()}_to_{end_date.isoformat()}.csv"

    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/ai/suggest-category", response_model=AiSuggestCategoryResponse)
def ai_suggest_category(payload: AiSuggestCategoryRequest):
    if payload.amount <= 0:
        raise HTTPException(status_code=422, detail="金额必须大于 0")

    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=422, detail="备注不能为空")

    categories_text = "、".join(AI_ALLOWED_CATEGORIES)

    system_prompt = (
        "你是一个消费记账应用里的分类助手。"
        "你只能从给定分类列表中选择一个分类。"
        "不要编造新分类。"
        "不要输出多余解释。"
        "必须返回 JSON。"
    )

    user_prompt = (
        f"消费金额：{payload.amount} 元\n"
        f"消费备注：{note}\n"
        f"可选分类：{categories_text}\n\n"
        '请返回严格 JSON：\n'
        '{\n'
        '  "category": "分类名",\n'
        '  "reason": "一句话理由"\n'
        '}'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = call_deepseek(messages, temperature=0.1, max_tokens=200)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后再试")

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试")

    category = data.get("category", "其他")
    if category not in AI_ALLOWED_CATEGORIES:
        category = "其他"

    reason = data.get("reason", "")
    if not reason:
        reason = "根据备注内容自动判断。"

    # Truncate reason to roughly 80 Chinese characters (240 bytes / 3)
    if len(reason) > 80:
        reason = reason[:80]

    return AiSuggestCategoryResponse(category=category, reason=reason)


@app.post("/ai/optimize-note", response_model=AiOptimizeNoteResponse)
def ai_optimize_note(payload: AiOptimizeNoteRequest):
    note = payload.note.strip()
    if not note:
        raise HTTPException(status_code=422, detail="备注不能为空")

    system_prompt = (
        "你是个人记账应用里的消费备注优化助手。"
        "只把用户输入的消费备注改写成更清晰、简短、适合记账的中文备注。"
        "不要改变消费事实。"
        "不要编造金额、日期、地点、健康信息。"
        "不要输出解释。"
        "不要输出多句话。"
        "不要超过 15 个中文字符。"
        "必须返回 JSON。"
    )

    user_prompt = (
        f"原始备注：{note}\n\n"
        '请返回严格 JSON：\n'
        '{\n'
        '  "optimized_note": "优化后的备注"\n'
        '}'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = call_deepseek(messages, temperature=0.2, max_tokens=120)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后再试")

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试")

    optimized_note = data.get("optimized_note", "")
    if not optimized_note:
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试")

    optimized_note = optimized_note.strip()

    # Cap at roughly 20 Chinese characters
    if len(optimized_note) > 20:
        optimized_note = optimized_note[:20]

    return AiOptimizeNoteResponse(optimized_note=optimized_note)

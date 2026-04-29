import json
import logging
from collections.abc import Mapping

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai_client import call_deepseek
from app.schemas import (
    AiMonthlyAdviceResponse,
    AiOptimizeNoteRequest,
    AiOptimizeNoteResponse,
    AiSuggestCategoryRequest,
    AiSuggestCategoryResponse,
)
from app.services.expense_service import (
    AI_ALLOWED_CATEGORIES,
    classify_expense,
    monthly_summary,
)


logger = logging.getLogger(__name__)

MONTHLY_ADVICE_SYSTEM_PROMPT = (
    "你是一个个人攒钱和消费记录应用里的 AI 消费分析助手。"
    "你要基于用户提供的消费统计数据，给出理性、克制、可执行的中文建议。"
    "不要编造不存在的收入、目标金额或身体健康信息。"
    "不要使用夸张语气。"
    "不要输出医疗、投资、贷款建议。"
)

CATEGORY_SYSTEM_PROMPT = (
    "你是一个消费记账应用里的分类助手。"
    "你只能从给定分类列表中选择一个分类。"
    "不要编造新分类。"
    "不要输出多余解释。"
    "必须返回 JSON。"
)

NOTE_SYSTEM_PROMPT = (
    "你是个人记账应用里的消费备注优化助手。"
    "只把用户输入的消费备注改写成更清晰、简短、适合记账的中文备注。"
    "不要改变消费事实。"
    "不要编造金额、日期、地点、健康信息。"
    "不要输出解释。"
    "不要输出多句话。"
    "不要超过 15 个中文字符。"
    "必须返回 JSON。"
)


def parse_ai_json_object(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试") from None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试") from None

    if not isinstance(data, Mapping):
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试")
    return dict(data)


def get_monthly_advice(db: Session, month: str) -> AiMonthlyAdviceResponse:
    summary = monthly_summary(db, month)
    if summary.count == 0:
        return AiMonthlyAdviceResponse(
            month=month,
            advice="这个月还没有消费记录，暂时无法生成 AI 消费分析。你可以先记录几笔消费后再试。",
        )

    category_lines = "\n".join(
        f"- {item.category}：{item.total_amount} 元（{item.count} 笔）"
        for item in summary.items
    )
    user_prompt = (
        f"月份：{month}\n"
        f"本月总消费：{summary.total_amount} 元\n"
        f"消费笔数：{summary.count} 笔\n"
        f"日均消费：{summary.average_daily_amount} 元\n"
        f"分类统计：\n{category_lines}\n\n"
        "请先用 1 句话总结本月消费情况，再给 3 条具体建议。每条建议要短。不超过 300 字。"
    )

    try:
        advice = call_deepseek(
            [
                {"role": "system", "content": MONTHLY_ADVICE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后再试") from exc

    return AiMonthlyAdviceResponse(month=month, advice=advice)


def suggest_category(payload: AiSuggestCategoryRequest) -> AiSuggestCategoryResponse:
    local_category = classify_expense(payload.note)
    categories_text = "、".join(AI_ALLOWED_CATEGORIES)
    user_prompt = (
        f"消费金额：{payload.amount} 元\n"
        f"消费备注：{payload.note}\n"
        f"可选分类：{categories_text}\n\n"
        "请返回严格 JSON：\n"
        "{\n"
        '  "category": "分类名",\n'
        '  "reason": "一句话理由"\n'
        "}"
    )

    try:
        raw = call_deepseek(
            [
                {"role": "system", "content": CATEGORY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        data = parse_ai_json_object(raw)
    except ValueError:
        return AiSuggestCategoryResponse(
            category=local_category,
            reason="未配置 AI 服务，已按本地规则推荐分类。",
        )
    except (RuntimeError, HTTPException) as exc:
        logger.info("AI category fallback: %s", type(exc).__name__)
        return AiSuggestCategoryResponse(
            category=local_category,
            reason="AI 分类暂不可用，已按本地规则推荐分类。",
        )

    category = data.get("category", local_category)
    if category not in AI_ALLOWED_CATEGORIES:
        category = local_category

    reason = str(data.get("reason") or "根据备注内容自动判断。").strip()
    return AiSuggestCategoryResponse(category=category, reason=reason[:80])


def optimize_note(payload: AiOptimizeNoteRequest) -> AiOptimizeNoteResponse:
    user_prompt = (
        f"原始备注：{payload.note}\n\n"
        "请返回严格 JSON：\n"
        "{\n"
        '  "optimized_note": "优化后的备注"\n'
        "}"
    )

    try:
        raw = call_deepseek(
            [
                {"role": "system", "content": NOTE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=120,
        )
        data = parse_ai_json_object(raw)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (RuntimeError, HTTPException) as exc:
        raise HTTPException(status_code=502, detail="AI 服务暂时不可用，请稍后再试") from exc

    optimized_note = str(data.get("optimized_note") or "").strip()
    if not optimized_note:
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试")

    return AiOptimizeNoteResponse(optimized_note=optimized_note[:20])

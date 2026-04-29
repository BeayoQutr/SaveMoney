from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai_client import is_ai_configured
from app.database import get_db
from app.schemas import (
    AiMonthlyAdviceResponse,
    AiOptimizeNoteRequest,
    AiOptimizeNoteResponse,
    AiSuggestCategoryRequest,
    AiSuggestCategoryResponse,
)
from app.services import ai_service


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    return {"ai_configured": is_ai_configured()}


@router.get("/monthly-advice", response_model=AiMonthlyAdviceResponse)
def ai_monthly_advice(month: str, db: Session = Depends(get_db)):
    return ai_service.get_monthly_advice(db, month)


@router.post("/suggest-category", response_model=AiSuggestCategoryResponse)
def ai_suggest_category(payload: AiSuggestCategoryRequest):
    return ai_service.suggest_category(payload)


@router.post("/optimize-note", response_model=AiOptimizeNoteResponse)
def ai_optimize_note(payload: AiOptimizeNoteRequest):
    return ai_service.optimize_note(payload)

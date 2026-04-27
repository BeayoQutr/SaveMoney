from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import GeneratePlanRequest, GeneratePlanResponse
from app.schemas import ExpenseCreateRequest, ExpenseCreateResponse
from app.budget_engine import generate_saving_plan

app = FastAPI(title="SaveMoney API")

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


@app.post("/expenses", response_model=ExpenseCreateResponse)
def create_expense(data: ExpenseCreateRequest):
    category = classify_expense(data.note)
    return ExpenseCreateResponse(
        amount=data.amount,
        note=data.note,
        date=data.date,
        category=category,
        message="消费记录成功"
    )

from fastapi import FastAPI

from app.schemas import GeneratePlanRequest, GeneratePlanResponse
from app.budget_engine import generate_saving_plan

app = FastAPI(title="SaveMoney API")


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
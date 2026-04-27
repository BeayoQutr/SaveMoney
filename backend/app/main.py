from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import GeneratePlanRequest, GeneratePlanResponse
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
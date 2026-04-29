from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import ai, expenses, plans


app = FastAPI(title="SaveMoney API")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router)
app.include_router(expenses.router)
app.include_router(ai.router)


@app.get("/")
def read_root():
    return {"message": "SaveMoney backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

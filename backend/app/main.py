from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_token
from app.database import Base, engine
from app.routers import ai, backup, expenses, plans


app = FastAPI(title="SaveMoney API")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plans.router, dependencies=[Depends(verify_token)])
app.include_router(expenses.router, dependencies=[Depends(verify_token)])
app.include_router(ai.router, dependencies=[Depends(verify_token)])
app.include_router(backup.router, dependencies=[Depends(verify_token)])


@app.get("/")
def read_root():
    return {"message": "SaveMoney backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

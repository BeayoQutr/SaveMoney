from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.auth import verify_token
from app.database import Base, engine
from app.db_migrations import ensure_sqlite_schema_compatibility
from app.error_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.routers import ai, backup, expenses, plans


app = FastAPI(title="SaveMoney API")
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

Base.metadata.create_all(bind=engine)
ensure_sqlite_schema_compatibility(engine)

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

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


_TEMP_DIR = tempfile.TemporaryDirectory()
_DB_PATH = Path(_TEMP_DIR.name) / "test.db"
os.environ["SAVEMONEY_DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models import Expense, SavingPlan  # noqa: E402


@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def api_client():
    return TestClient(fastapi_app)


@pytest.fixture
def db_path() -> Path:
    return _DB_PATH


@pytest.fixture(autouse=True)
def clean_database():
    db = SessionLocal()
    try:
        db.query(Expense).delete()
        db.query(SavingPlan).delete()
        db.commit()
    finally:
        db.close()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    os.environ.pop("SAVEMONEY_DATABASE_URL", None)
    _TEMP_DIR.cleanup()

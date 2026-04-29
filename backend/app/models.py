from datetime import UTC, datetime

from sqlalchemy import Column, Integer, Float, String, Date, DateTime

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    amount_cents = Column(Integer, nullable=True, default=None)
    note = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    category = Column(String, nullable=False)
    payment_method = Column(String, nullable=True, default=None)
    is_necessary = Column(Integer, nullable=True, default=None)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class SavingPlan(Base):
    __tablename__ = "saving_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_amount = Column(Float, nullable=False)
    target_amount_cents = Column(Integer, nullable=True, default=None)
    deadline = Column(Date, nullable=False)
    monthly_income = Column(Float, nullable=False)
    monthly_income_cents = Column(Integer, nullable=True, default=None)
    fixed_expenses = Column(Float, nullable=False)
    fixed_expenses_cents = Column(Integer, nullable=True, default=None)
    minimum_living_cost = Column(Float, nullable=False)
    minimum_living_cost_cents = Column(Integer, nullable=True, default=None)
    identity = Column(String, nullable=True, default=None)
    saved_amount = Column(Float, nullable=False, default=0.0)
    saved_amount_cents = Column(Integer, nullable=True, default=None)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

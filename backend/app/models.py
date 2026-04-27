from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, Date, DateTime

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    note = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
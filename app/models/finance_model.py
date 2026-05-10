from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database.database import Base


class FinanceRecord(Base):
    __tablename__ = "finance_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    record_date = Column(Date, default=date.today, index=True)
    income = Column(Float)
    fixed_expenses = Column(Float)
    variable_expenses = Column(Float)
    debt_payment = Column(Float)
    savings_current = Column(Float, nullable=True)
    goal_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship("User", back_populates="finance_records")
